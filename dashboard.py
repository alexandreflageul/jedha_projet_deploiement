#! /usr/bin/env python
# -*-coding:utf-8 -*-

## dashboard application


# Module
import streamlit as st
from streamlit_option_menu import option_menu
import math
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import requests



# Functions

# Main
def exploration():
    st.title("GETAROUND - Analyse des délais de rendu des véhicules")
    
    ## load data and cache them
    delai_file_path = "data/get_around_delay_analysis.xlsx"
    df = pd.read_excel(delai_file_path)
    
    st.divider()
    st.subheader("Le jeu de données")
    st.write(df.head())
    explain_data = st.checkbox('Explication des données ?')
    if explain_data:
        st.markdown("""
    * rental_id : identifiant de la location (unique)
    * car_id : identifiant du véhicule (peu apparaitre plusieurs fois)
    * checkin_type : methode utilisée pour louer le véhicule et le rendre (mobile = contrat signé sur smartphone ; connect = voiture équipée avec la technologie Connect)
    * state : status de la location ("ended" or "cancelled" [by the driver or owner]) 
    * delay_at_checkout_in_minutes : nombre de minute entre le moment réel du rendu et le moment prévu du rendu (valeur négative signifie véhicule retourné en avance)
    * previous_ended_rental_id : identifiant de la location précédente si survenue moins de 12h avant, une valeur Null signifie pas de location avant ou alors location précédente de plus de 12h)
    * time_delta_with_previous_rental_in_minutes : délai (en minute) entre deux location (entre la fin théorique et le début théorique des localtion N et N+1 respectivement), si Null, alors plus de 12h entre les locations
    """)
        st.info("""NB: les valeurs manquantes des colonnes "previous_ended_rental_id" et "time_delta_with_previous_rental_in_minutes" n'en sont pas, ce sont des indications de délais supérieurs à 12h.""")
        st.info("""NB: Pour une raison inconnue, il y a des valeurs manquantes dans la colonne "delay_at_checkout_in_minutes" \
                alors même que les locations se sont terminées et que les véhicules ont été rendus. \
                Ces lignes ont donc été retirée""")
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        @st.cache_data
        def display_fig1(data):
            fig1 = sns.displot(data=data, x="state")
            plt.title("Répartition des locations annulées ou réalisées")
            plt.text(-0.15, 1000, f"{round(100*(data['state']=='canceled').sum()/len(data), 2)} %")
            plt.text(0.85, 1000, f"{round(100*(data['state']=='ended').sum()/len(data), 2)} %")
            return fig1
    
        st.write(f"le jeu de donnée comporte au total {len(df)} locations dont certaines correspondent à des locations annulées.")
        st.pyplot(display_fig1(df))
    
    with col2:
        @st.cache_data
        def display_fig2(df):
           fig2, ax2 = plt.subplots()
           sns.histplot(df["rental_id"])
           plt.title("Répartition du nombre de location par voiture")
           plt.xlabel("nombre de fois qu'une voiture est louée")
           plt.ylabel("nombre de voiture à être louée X fois")
           return fig2
    
        nombre_de_voiture = len(set(df['car_id']))
        nombre_de_location_par_voiture = st.slider("Nombre de voiture louées au maximum X fois : ", 0, 40, value=4)
        serie = df.groupby("car_id").count()
        poucentage_loc_number = round(100 * (serie['rental_id'] <= nombre_de_location_par_voiture).sum() / nombre_de_voiture, 2)
        st.write(f"Ces locations concernent un total de {nombre_de_voiture} voitures, dont {poucentage_loc_number}% sont louées {nombre_de_location_par_voiture} fois ou moins.")
        st.pyplot(display_fig2(serie))
    
    
    
    st.divider()
    # section d'analyse de l'établissement d'un seuil, combien de location enregistrée aurait été possible ?
    
    df_ended = df[df.state=="ended"]
    df_ended = df_ended[df_ended.delay_at_checkout_in_minutes.isnull() == False]
    
    def display_fig3(data, threshold):
        fig, ax = plt.subplots()
        sns.histplot(data.time_delta_with_previous_rental_in_minutes)
        plt.axvline(x=threshold, ymin=0.01, ymax=0.95, color='b', label='seuil')
        plt.title("Distribution des délais entre deux locations (moins de 12h (720min) entre les deux)")
        plt.xlabel("minutes")
        plt.ylabel("Nombre de location")
        plt.legend()
        return fig
    
    st.subheader("Combien de locations auraient été impactées par l'existence d'un délai d'interdiction de location entre deux réservations ?")
    percent_less_than_12h = round(100 - (100 * df_ended.previous_ended_rental_id.isnull().sum()/len(df_ended)), 2)
    st.write(f"Parmi toutes les locations qui se sont terminées, seulement {percent_less_than_12h}% ont une location antérieure datant de moins de 12h.")
    st.write(f"Ce sont donc ces locations qui pourront être impactées par l'établissement d'un délai minimal de 'jachère' entre deux locations.")
    
    threshold = st.slider("Seuil d'interdiction de location (en min) après le rendu **prévu** du véhicule", 0, 600, 240, step=10)
    data = df_ended["time_delta_with_previous_rental_in_minutes"]
    possible_location = sum([1 for x in data if math.isnan(x) or x > threshold])
    percent_possible = round(possible_location * 100 / len(df_ended), 2)
    st.write(f"""
    Sur la base des informations de fin et de début des locations N et N+1 respectivement,
    l'utilisation d'un **seuil de {threshold} min, rend possible {percent_possible} %** des locations du jeu de données.
    """)
    
    
    st.write("Ci-dessous, la distribution des délai entre le rendu et la remise en location des véhicules, avec établissement d'un seuil (barre vertical) interdisant les locations des véhicules dans un certain lapse de temps")
    st.pyplot(display_fig3(df_ended[df_ended.time_delta_with_previous_rental_in_minutes.isnull() == False], threshold))
    
    
    st.divider()
    
    # analyse de la distribution du délai de retour des véhicules par rapport au moment de retour prévu
    # tout véhicule confondu
    
    @st.cache_data
    def display_fig4(data):
        fig4, ax3 = plt.subplots()
        sns.histplot(data)
        #ax3.hist(df_ended["delay_at_checkout_in_minutes"], bins=20)
        plt.xlim((-720, 720))
        plt.title(f"Analyse des délais de retour des véhicules par rapport au moment prévu (0)\nles délais au dela de l'étendu [-720, 720] minutes ne sont pas montrés")
        plt.xlabel("Nombre de minutes par rapport au moment de retour prévu")
        plt.ylabel("Nombre de retour")
        return fig4
    
    st.subheader("Analyse des délais de retour de véhicules - colonne delay_at_checkout_in_minutes")
    
    data2 = df_ended["delay_at_checkout_in_minutes"]
    in_range = sum([ 1 for x in data2 if -720 <= x <= 720 ])
    percent_in_range = round(100 * in_range / len(data2), 2)
    st.write(f"""{percent_in_range} % des véhicules sont retournés dans l'étendue [-720, 720] minutes autour du moment prévu de retour. Les rendus au dela de cette étendue sont considérés ici comme des anomalies""")
    st.pyplot(display_fig4(data2))
    
    df_ended2 = df_ended.query("-720 <= delay_at_checkout_in_minutes <= 720")
    data3 = df_ended2["delay_at_checkout_in_minutes"]
    
    #borne_sup = st.slider("Choix des bornes", 0, 720, value=threshold, step=10)
    
    before_threshold = round(100 * sum([ 1 for x in data3 if x <= threshold ]) / len(data3), 2)
    st.write(f"Parmi ces véhicules, {before_threshold}% sont retourné avant le seuil de {threshold} minutes.")
    
    
    st.divider()
    
    st.subheader("Evaluation de la mise en place d'une durée de jachère post locative")
    df_ended = df[df.state=="ended"]
    
    df_ended = df_ended[df_ended.delay_at_checkout_in_minutes.isnull() == False]
    data1 = df_ended["time_delta_with_previous_rental_in_minutes"]
    
    df_ended2 = df_ended.query("-720 <= delay_at_checkout_in_minutes <= 720")
    data2 = df_ended2["delay_at_checkout_in_minutes"]
    
    x_values = []
    percent_possible_possible = []
    pourcentage_voiture_rendu = []
    for delay_threshold in range(0, 721, 10):
        possible_location = sum([1 for x in data1 if math.isnan(x) or x >= delay_threshold])
        x_values.append(delay_threshold)
        percent_possible_possible.append(round(possible_location * 100 / len(data1), 2))
        pourcentage_voiture_rendu.append(round(100 * sum([ 1 for x in data2 if x <= delay_threshold ]) / len(data2), 2))
    
    @st.cache_data
    def draw_fig5(percent_possible_possible, pourcentage_voiture_rendu, threshold):
        fig, ax = plt.subplots()
        sns.lineplot(x=x_values, y=percent_possible_possible, label="Pourcentage de location possible")
        sns.lineplot(x=x_values, y=pourcentage_voiture_rendu, label="Pourcentage de véhicule retournés")
        plt.title("Evaluation des effets de la mise en place d'une durée de jachère post locative\npendant laquelle toute location est interdite.")
        plt.xlabel("Durée du seuil en minute")
        plt.ylabel("Pourcentage")
        plt.axvline(x=threshold, ymin=0, color="green", label="seuil")
        plt.legend()
        return fig
    
    
    st.pyplot(draw_fig5(percent_possible_possible, pourcentage_voiture_rendu, threshold))
    




def prediction():
    with st.form("prediction", clear_on_submit=True):
        st.title("Estimer votre gain journalier si vous louer votre véhicule !")
    
        vehicule_list = ['Audi',
                         'BMW',
                         'Citroën',
                         'Ferrari',
                         'Maserati',
                         'Mercedes',
                         'Mitsubishi',
                         'Nissan',
                         'Opel',
                         'PGO',
                         'Peugeot',
                         'Renault',
                         'SEAT',
                         'Subaru',
                         'Toyota',
                         'Volkswagen']

        marque = st.radio("Marque de véhicule :", vehicule_list, horizontal=True)
        kilometrage = st.text_input("Kilometrage")
        puissance = st.text_input("Puissance du moteur")
    
        carburant_list = ['diesel', 'hybrid_petrol', 'petrol']
        carburant = st.radio("Carburant :", carburant_list, horizontal=True)
    
        colors_list = ['beige',
                       'black',
                       'blue',
                       'brown',
                       'green',
                       'grey',
                       'orange',
                       'red',
                       'silver',
                       'white']
        couleur = st.radio("Couleur du véhicule :", colors_list, horizontal=True)
    
        voiture_type_list = ['convertible',
                             'coupe',
                             'estate',
                             'hatchback',
                             'sedan',
                             'subcompact',
                             'suv',
                             'van']
        voiture_type = st.radio("Quel est le type du véhicule", voiture_type_list, horizontal=True)
    
        options_list = ["private_parking_available", "has_gps", "has_air_conditioning", "automatic_car", "has_getaround_connect", "has_speed_regulator", "winter_tires"]
        options = st.multiselect("Sélectionner les options de votre véhicule :", options_list)
        option_level = len(options)
    
        button = st.form_submit_button("Estimer le montant de votre location !")

        if button:
            url = ""
            input_data_list = [marque, int(kilometrage), int(puissance), carburant, couleur, voiture_type, option_level]
            response = requests.post(url=url, json={"input_data": input_data_list})
            result = response.json()
            st.success(f"Prédictions : {result['predictions']}")


def visualise_code():
    st.title("Dans cette section, vous pouvez visualiser le code source de cette aplication streamlit, ainsi que celui de l'API.")
    # visualiser le code streamlit
    button_st = st.checkbox("Visualiser le code streamlit")
    if button_st:
        with open("./dashboard.py", "r") as filin1:
            st.code("".join(filin1.readlines()))

    # visualiser le code fastAPI
    button_api = st.checkbox("Visualiser le code FastAPI")
    if button_api:
        with open("./app.py", "r") as filin2:
            st.code("".join(filin2.readlines()))


st.set_page_config( page_title="Getaround dashboard",
                    page_icon="",
                    layout="wide")#"centered")

with st.sidebar:
    app_name = "Jedha projet déploiement\nGetAround analysis"
    sections = ["Exploration", "Prédiction de prix", "Visualiser le code source"]
    icones = ["book", "kanban", "code-square"]
    styles = {
       "container": {"padding": "5!important", "background-color": "#fafafa"},
       "icon": {"color": "orange", "font-size": "25px"}, 
       "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
       "nav-link-selected": {"background-color": "#02ab21"},
    }
    
    choose = option_menu(app_name, sections,
                         icons=icones,
                         menu_icon="app-indicator", default_index=0,
                         styles=styles)


if choose == "Exploration":
    exploration()
elif choose == "Prédiction de prix":
    prediction()
elif choose == "Visualiser le code source":
    visualise_code()
