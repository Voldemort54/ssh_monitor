import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import urllib.request
import csv
import io
import re
import ipaddress
from datetime import datetime, timedelta
import time
import calendar
import joblib
import hashlib
import chardet
from maxminddb import open_database

# =====================================
# CONFIGURATION DU CACHE
# =====================================
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(file_content, params):
    hash_obj = hashlib.sha256()
    hash_obj.update(file_content)
    hash_obj.update(str(params).encode('utf-8'))
    return hash_obj.hexdigest()

def cached_load(content, params):
    cache_key = get_cache_key(content, params)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.joblib")

    if os.path.exists(cache_path):
        st.info("📦 Chargement des données depuis le cache...")
        return joblib.load(cache_path)
    return None

def save_to_cache(content, params, data):
    cache_key = get_cache_key(content, params)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.joblib")
    joblib.dump(data, cache_path)
    return cache_path

# =====================================
# TÉLÉCHARGEMENT BASE GÉOLOCALISATION
# =====================================
GEOIP_URL = "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"
GEOIP_PATH = "GeoLite2-City.mmdb"

def download_geoip():
    if not os.path.exists(GEOIP_PATH):
        try:
            with st.spinner('📡 Téléchargement de la base de géolocalisation...'):
                urllib.request.urlretrieve(GEOIP_URL, GEOIP_PATH)
            st.success('✅ Base géolocalisation téléchargée!')
            time.sleep(1)
            return True
        except Exception as e:
            st.error(f"Échec du téléchargement : {e}")
            return False
    return True

download_success = download_geoip()

# =====================================
# FONCTIONS UTILITAIRES
# =====================================
def categorize_event(message):
    msg = str(message).lower()
    if "failed password" in msg:
        return "Tentative Échouée"
    elif "accepted password" in msg:
        return "Connexion Réussie"
    elif "invalid user" in msg:
        return "Utilisateur Invalide"
    elif "break-in" in msg or "intrusion" in msg:
        return "Tentative d'Intrusion"
    elif "disconnected" in msg:
        return "Déconnexion"
    elif "session opened" in msg:
        return "Session Ouverte"
    elif "session closed" in msg:
        return "Session Fermée"
    else:
        return "Autre Événement"

def clean_ip(ip_str):
    if not ip_str or pd.isna(ip_str) or ip_str in ['', 'unknown']:
        return "IP Inconnue"

    # Extraction de l'IP avec regex
    match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', str(ip_str))
    if match:
        ip = match.group(0)
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            return "IP Invalide"
    return "IP Inconnue"

# Cache pour la géolocalisation
ip_location_cache = {}
geo_reader = None

def init_geo_reader():
    global geo_reader
    if geo_reader is None and os.path.exists(GEOIP_PATH):
        try:
            geo_reader = open_database(GEOIP_PATH)
        except Exception as e:
            st.error(f"Erreur d'initialisation GeoLite2: {e}")
    return geo_reader

def get_location(ip):
    global geo_reader

    if ip in ["IP Inconnue", "IP Invalide", "localhost", "127.0.0.1"] or not download_success:
        return ("Localisation Inconnue", None, None)

    if ip in ip_location_cache:
        return ip_location_cache[ip]

    try:
        if geo_reader is None:
            init_geo_reader()

        if geo_reader:
            match = geo_reader.get(ip)
            if match:
                city = match.get('city', {}).get('names', {}).get('fr', '')
                country = match.get('country', {}).get('names', {}).get('fr', match.get('country', {}).get('iso_code', ''))
                latitude = match.get('location', {}).get('latitude')
                longitude = match.get('location', {}).get('longitude')

                location_text = ""
                if city:
                    location_text += city
                if country:
                    if location_text:
                        location_text += ", "
                    location_text += country

                if not location_text:
                    location_text = "Localisation Inconnue"

                location = (location_text, latitude, longitude)
            else:
                location = ("Localisation Inconnue", None, None)
        else:
            location = ("Base GeoLite absente", None, None)

        ip_location_cache[ip] = location
        return location
    except Exception as e:
        st.error(f"Erreur de géolocalisation pour {ip}: {str(e)}")
        return ("Erreur de Géolocalisation", None, None)

# =====================================
# CHARGEMENT DES DONNÉES
# =====================================
def load_data(file, enable_geo=True, sample_size=None):
    try:
        content = file.getvalue()
        cache_params = {
            'enable_geo': enable_geo,
            'sample_size': sample_size,
            'file_size': len(content)
        }

        # Vérification du cache
        cached_data = cached_load(content, cache_params)
        if cached_data is not None:
            return cached_data

        with st.spinner('🔍 Analyse du fichier en cours...'):
            # Détection de l'encodage
            raw_content = file.getvalue()
            encoding = chardet.detect(raw_content)['encoding'] or 'utf-8'

            # Diagnostic: nombre de lignes
            raw_lines = raw_content.decode(encoding, errors='replace').splitlines()
            line_count = len(raw_lines)
            st.info(f"⚙️ Fichier brut: {line_count} lignes détectées")

            # Lecture CSV robuste
            df = pd.DataFrame()
            try:
                # Lecture avec csv.reader pour une meilleure gestion
                reader = csv.reader(io.StringIO(raw_content.decode(encoding, errors='replace')), 
                                   delimiter=';',
                                   quoting=csv.QUOTE_NONE)

                data = []
                for row in reader:
                    # Ajouter des colonnes manquantes si nécessaire
                    if len(row) < 8:
                        row += [''] * (8 - len(row))
                    # Fusionner les colonnes supplémentaires dans le message
                    elif len(row) > 8:
                        row[7] = ';'.join(row[7:])
                        row = row[:8]
                    data.append(row)

                # Création du DataFrame
                columns = ['Timestamp', 'Lab', 'Service', 'PID', 'IP', 'User', 'EventCode', 'Message']
                df = pd.DataFrame(data, columns=columns)

            except Exception as e:
                st.error(f"Erreur de lecture CSV: {e}")
                return pd.DataFrame()

            st.info(f"📥 {len(df)} lignes chargées après traitement CSV")

            # Conversion des timestamps (sans supprimer les invalides)
            df['Timestamp'] = pd.to_datetime(
                df['Timestamp'], 
                errors='coerce',
                format='mixed'
            )

            # Marquer les timestamps invalides mais conserver les lignes
            invalid_ts = df['Timestamp'].isna().sum()
            if invalid_ts > 0:
                st.warning(f"⚠️ {invalid_ts} timestamps invalides - conservation des lignes")
                # Remplacer par la date actuelle
                df.loc[df['Timestamp'].isna(), 'Timestamp'] = pd.Timestamp.now()

            # Nettoyage des IPs
            df['IP'] = df['IP'].apply(clean_ip)

            # Extraction d'IP depuis les messages
            missing_ip_mask = df['IP'].isin(['IP Inconnue', 'IP Invalide'])
            if missing_ip_mask.any():
                extracted = df.loc[missing_ip_mask, 'Message'].str.extract(
                    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', 
                    expand=False
                )
                df.loc[missing_ip_mask, 'IP'] = extracted.fillna('IP Inconnue')

            # Catégorisation des événements
            df['EventCategory'] = df['Message'].apply(categorize_event)

            # Colonnes temporelles
            df['Hour'] = df['Timestamp'].dt.hour
            df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
            df['Date'] = df['Timestamp'].dt.date

            # Échantillonnage optionnel
            if sample_size and len(df) > sample_size:
                original_count = len(df)
                df = df.sample(sample_size)
                st.warning(f"⚠️ Échantillonnage: {sample_size}/{original_count} lignes")
            else:
                st.info(f"📊 {len(df)} lignes conservées")

            # Géolocalisation
            if enable_geo and download_success:
                st.info("🌍 Début de la géolocalisation...")
                progress_bar = st.progress(0)

                # Optimisation: traitement des IPs uniques
                unique_ips = df['IP'].unique()
                location_map = {}

                for i, ip in enumerate(unique_ips):
                    location_map[ip] = get_location(ip)
                    progress_bar.progress((i + 1) / len(unique_ips))

                # Application des localisations
                df['Location'] = df['IP'].map(lambda ip: location_map[ip][0])
                df['lat'] = df['IP'].map(lambda ip: location_map[ip][1])
                df['lon'] = df['IP'].map(lambda ip: location_map[ip][2])

                progress_bar.empty()
                st.success(f"✅ Géolocalisation de {len(unique_ips)} IPs terminée")
            else:
                df['Location'] = "Géolocalisation désactivée"
                df['lat'] = None
                df['lon'] = None

            # Sauvegarde dans le cache
            save_to_cache(content, cache_params, df)
            st.success(f"✅ Chargement final: {len(df)} lignes")
            return df

    except Exception as e:
        st.error(f"ERREUR CRITIQUE: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

# =====================================
# INTERFACE UTILISATEUR
# =====================================
st.set_page_config(
    page_title="SSH Sentinel Pro",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔒 SSH Sentinel Pro - Analyse de Sécurité")
st.caption("Analyse avancée des journaux d'authentification SSH")

st.sidebar.header("📤 Téléversement de Fichier")
uploaded_file = st.sidebar.file_uploader(
    "Choisissez un fichier CSV de logs SSH",
    type=["csv"],
    help="Format: Timestamp;Lab;Service;PID;IP;User;EventCode;Message"
)

st.sidebar.header("⚙️ Options")
enable_geo = st.sidebar.checkbox("Activer la géolocalisation", value=True)

# Échantillonnage optionnel (désactivé par défaut)
st.sidebar.markdown("**Échantillonnage**")
sample_option = st.sidebar.radio(
    "Mode d'échantillonnage:",
    ["Toutes les lignes", "Échantillon personnalisé"],
    index=0
)

sample_size = None
if sample_option == "Échantillon personnalisé":
    sample_size = st.sidebar.number_input(
        "Nombre de lignes à échantillonner",
        min_value=1000,
        max_value=1000000,
        value=50000,
        step=1000
    )

if uploaded_file is not None:
    with st.spinner('Chargement des données...'):
        df = load_data(uploaded_file, enable_geo, sample_size)

    if not df.empty:
        st.success(f"✅ Fichier chargé: {len(df)} événements")

        # Filtres temporels
        st.sidebar.header("⏱ Filtres Temporels")
        min_date = df['Timestamp'].min().to_pydatetime()
        max_date = df['Timestamp'].max().to_pydatetime()

        date_range = st.sidebar.date_input(
            "Plage de dates",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            end_date += timedelta(days=1)  # Inclure toute la journée
            filtered_df = df[(df['Timestamp'] >= pd.Timestamp(start_date)) & 
                             (df['Timestamp'] <= pd.Timestamp(end_date))]
            st.sidebar.info(f"Filtre: {len(filtered_df)} événements")
        else:
            filtered_df = df
            st.sidebar.warning("Sélectionnez une plage valide")

        # Filtres supplémentaires
        st.sidebar.header("🔍 Filtres Avancés")

        # Par catégorie d'événement
        event_types = filtered_df['EventCategory'].unique()
        selected_events = st.sidebar.multiselect(
            "Types d'événements",
            options=event_types,
            default=event_types
        )
        if selected_events:
            filtered_df = filtered_df[filtered_df['EventCategory'].isin(selected_events)]

        # Par IP (sans exclure "IP Inconnue")
        top_ips = filtered_df['IP'].value_counts().index
        selected_ips = st.sidebar.multiselect("Adresses IP", options=top_ips)
        if selected_ips:
            filtered_df = filtered_df[filtered_df['IP'].isin(selected_ips)]

        # Par utilisateur
        users = filtered_df['User'].unique()
        selected_users = st.sidebar.multiselect("Utilisateurs", options=users)
        if selected_users:
            filtered_df = filtered_df[filtered_df['User'].isin(selected_users)]

        st.sidebar.info(f"📊 {len(filtered_df)} événements filtrés")

        # Onglets
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Tableau de Bord", 
            "🗺 Carte", 
            "📈 Statistiques", 
            "🔍 Détails"
        ])

        with tab1:
            # KPI
            col1, col2, col3 = st.columns(3)
            col1.metric("Événements", len(filtered_df))
            col2.metric("IPs Uniques", filtered_df['IP'].nunique())
            failed = len(filtered_df[filtered_df['EventCategory'] == "Tentative Échouée"])
            col3.metric("Tentatives Échouées", failed)

            # Activité horaire
            st.subheader("⏱ Activité Horaire")
            hourly = filtered_df.groupby('Hour').size().reset_index(name='Count')
            fig = px.line(hourly, x='Hour', y='Count', title='Activité par Heure')
            st.plotly_chart(fig, width='stretch')

            # CORRECTION FINALE : ACTIVITÉ JOURNALIÈRE
            st.subheader("📅 Activité Journalière")
            
            # 1. Grouper par jour (dates réelles)
            daily_counts = filtered_df.groupby(
                filtered_df['Timestamp'].dt.date
            ).size().reset_index(name='Count')
            
            # 2. Convertir en datetime
            daily_counts['Date'] = pd.to_datetime(daily_counts['Timestamp'])
            
            # 3. Déterminer les dates min et max des données
            min_date_graph = daily_counts['Date'].min()
            max_date_graph = daily_counts['Date'].max()
            
            # 4. Créer une plage complète de dates UNIQUEMENT entre min et max
            full_date_range = pd.date_range(
                start=min_date_graph,
                end=max_date_graph,
                freq='D'
            )
            
            # 5. Réindexer pour avoir toutes les dates dans la plage
            daily_counts = daily_counts.set_index('Date')
            daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
            daily_counts = daily_counts.reset_index()
            
            # 6. Renommer les colonnes (seulement 2 colonnes)
            daily_counts.columns = ['Date', 'Count']
            
            # 7. Créer le graphique avec les limites exactes
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_counts['Date'], 
                y=daily_counts['Count'],
                mode='lines+markers',
                line_shape='linear',
                connectgaps=False
            ))
            
            # 8. Limiter strictement l'axe X aux dates extrêmes
            fig.update_xaxes(
                range=[min_date_graph - timedelta(days=1), max_date_graph + timedelta(days=1)],
                constrain='domain'
            )
            
            fig.update_layout(
                title='Activité par Jour',
                xaxis_title='Date',
                yaxis_title='Nombre d\'événements',
                showlegend=False
            )
            
            st.plotly_chart(fig, width='stretch')

            # Top IPs (incluant "IP Inconnue")
            st.subheader("🔝 Top 10 IPs")
            top_ips = filtered_df['IP'].value_counts().head(10).reset_index()
            top_ips.columns = ['IP', 'Tentatives']
            st.dataframe(top_ips, width='stretch')

        with tab2:
            # Carte géographique
            st.subheader("🌍 Carte des Tentatives")

            if enable_geo and download_success and not filtered_df.empty:
                # Préparation des données
                geo_data = filtered_df.dropna(subset=['lat', 'lon'])

                if not geo_data.empty:
                    # Agrégation par localisation
                    agg_data = geo_data.groupby(['lat', 'lon', 'Location']).size().reset_index(name='Count')

                    # Création de la carte
                    fig = px.scatter_mapbox(
                        agg_data,
                        lat='lat',
                        lon='lon',
                        size='Count',
                        color='Count',
                        hover_name='Location',
                        zoom=1,
                        color_continuous_scale=px.colors.sequential.OrRd,
                    )
                    fig.update_layout(
                        mapbox_style="open-street-map",
                        height=700,
                        margin={"r":0,"t":0,"l":0,"b":0}
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.warning("Aucune donnée géographique valide")
            else:
                st.warning("Géolocalisation désactivée ou échouée")

            # Distribution géographique
            st.subheader("🗺 Distribution par Pays (Top 20)")
            if not filtered_df.empty and 'Location' in filtered_df.columns:
                loc_counts = filtered_df['Location'].value_counts().head(20).reset_index()
                loc_counts.columns = ['Location', 'Count']
                fig = px.bar(loc_counts, x='Location', y='Count', title="Top 20 des Localisations")
                st.plotly_chart(fig, width='stretch')

        with tab3:
            # Répartition des événements
            st.subheader("📊 Types d'Événements")
            if not filtered_df.empty:
                event_counts = filtered_df['EventCategory'].value_counts().reset_index()
                event_counts.columns = ['Category', 'Count']
                fig = px.pie(event_counts, names='Category', values='Count')
                st.plotly_chart(fig, width='stretch')

        with tab4:
            # Détails
            st.subheader("📋 Détails des Événements")
            if not filtered_df.empty:
                st.dataframe(filtered_df.sort_values('Timestamp', ascending=False).head(100), width='stretch')

            # Messages fréquents
            st.subheader("💬 Messages Fréquents")
            if not filtered_df.empty:
                msg_counts = filtered_df['Message'].value_counts().head(10).reset_index()
                msg_counts.columns = ['Message', 'Count']
                st.dataframe(msg_counts, width='stretch')

        # Export
        st.sidebar.header("Export")
        if st.sidebar.button("Exporter les données"):
            if not filtered_df.empty:
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.sidebar.download_button(
                    label="Télécharger CSV",
                    data=csv_data,
                    file_name=f"ssh_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
    else:
        st.error("Erreur lors du chargement des données")
else:
    st.warning("⚠️ Veuillez téléverser un fichier de logs SSH")

# Gestion du cache
st.sidebar.header("Cache")
if st.sidebar.button("Vider le cache"):
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".joblib"):
            os.remove(os.path.join(CACHE_DIR, f))
    st.sidebar.success("Cache vidé!")

# Pied de page
st.sidebar.markdown("---")
st.sidebar.markdown("**SSH Sentinel Pro** v5.1")
st.sidebar.markdown("Système d'analyse de sécurité SSH")
