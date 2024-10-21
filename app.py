import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pydeck
from datetime import datetime

#@st.cache_data
def cargar_contagios():
    data = pd.read_excel('streamlitcovid.xlsx', sheet_name='contagios')
    return data

#@st.cache_data
def cargar_departamentos():
    data = pd.read_excel('streamlitcovid.xlsx', sheet_name='departamentos')
    return data


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Datos", "Lineas", "Barras", "Mapa", "Circular", "Histograma"])


df_contagios = cargar_contagios()
df_departamentos = cargar_departamentos()

df_join = df_contagios.join(df_departamentos.set_index('departamento'), on='departamento', validate='m:1')
df_join['fecha_diagnostico'] = df_join['fecha_diagnostico'].str[:10]
df_join['fecha_muerte'] = df_join['fecha_muerte'].str[:10]
#df_join['fecha_diagnostico'] = pd.to_datetime(df_join['fecha_diagnostico'])
#df_join['fecha_muerte'] = pd.to_datetime(df_join['fecha_muerte'])


with tab1:
    #Codigo Dataframe y Metrics
    ver_df = st.checkbox("Ver Dataframe")
    #ver_df = st.checkbox("Ver Dataframe")

    if ver_df:
        st.write(df_join)
    
    confirmados = df_join.id_de_caso.count()
    recuperados = (df_join['recuperado'] == 'Recuperado').sum()
    fallecidos = (df_join['recuperado'] == 'Fallecido').sum()
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Casos confirmados", value=confirmados)
    col2.metric(label="Recuperados", value=recuperados)
    col3.metric(label="Fallecidos", value=fallecidos)

with tab2:
    with st.container(border=True):
        st.header('Contagios x Fecha')
        fecha1 = datetime.strptime(df_join['fecha_diagnostico'].min(), '%Y-%m-%d')
        fecha2 = datetime.strptime(df_join['fecha_diagnostico'].max(), '%Y-%m-%d')
        slider_fechas = st.slider(
            "Seleccione un rango de fechas", 
            min_value=fecha1,
            max_value=fecha2, 
            value=(fecha1, fecha2)
        )
        valor1 = slider_fechas[0].strftime('%Y-%m-%d')
        valor2 = slider_fechas[1].strftime('%Y-%m-%d')
        df_filtro_contagio_fecha = df_join[(df_join['fecha_diagnostico'] >= valor1) & (df_join['fecha_diagnostico'] <= valor2)]
        df_contagios_fecha = df_filtro_contagio_fecha.groupby(['fecha_diagnostico']).count()['id_de_caso']

        st.line_chart(df_contagios_fecha)

    with st.container(border=True):
        st.header('Fallecidos x Fecha')
        df_fallecidos = df_join[df_join['recuperado'] == 'Fallecido']
        opciones = df_fallecidos['fecha_muerte'].sort_values().unique()
        fecha1m = df_fallecidos['fecha_muerte'].min()
        fecha2m = df_fallecidos['fecha_muerte'].max()
        slider_fechas_fallecidos = st.select_slider(
            "Seleccione un rango de fechas",
            options=opciones,
            value=(fecha1m, fecha2m)
        )
        valor1m = slider_fechas_fallecidos[0]
        valor2m = slider_fechas_fallecidos[1]
        df_filtro_fallecidos_fecha = df_fallecidos[(df_fallecidos['fecha_muerte'] >= valor1m) & (df_fallecidos['fecha_muerte'] <= valor2m)]
        df_fallecidos_fecha = df_filtro_fallecidos_fecha.groupby(['fecha_muerte']).count()['id_de_caso']

        fig, ax = plt.subplots()
        ax.plot(df_fallecidos_fecha)
        ax.set_title('Fallecidos')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Cantidad')
        ax.tick_params(axis='x', labelrotation=90, labelsize=6)
        st.pyplot(fig)
        ax.clear()

with tab3:
    with st.container(border=True):
        departamentos = st.multiselect(
            "Seleccione los departamentos",
            df_join['departamento_nom'].sort_values().unique(),
            placeholder="Seleccione departamentos"
        )
        if len(departamentos) == 0:
            df_contagios_departamento = df_join.groupby(['departamento_nom']).count()['id_de_caso']
        else:
            df_filtro_departamentos = df_join[df_join['departamento_nom'].isin(departamentos)]
            df_contagios_departamento = df_filtro_departamentos.groupby(['departamento_nom']).count()['id_de_caso']

        st.header('Contagios x Departamento')
        st.bar_chart(df_contagios_departamento)

    df_fallecidos_departamento = df_fallecidos.groupby(['departamento_nom']).count()['id_de_caso']
    with st.container(border=True):
        st.header('Fallecidos x Departamento')
        st.bar_chart(df_fallecidos_departamento, horizontal=True)

with tab4:
    df_contagios_departamento_mapa = df_join.groupby(by=['departamento_nom', 'latitud', 'longitud'], as_index=False).id_de_caso.count()
    df_contagios_departamento_mapa['size'] = df_contagios_departamento_mapa['id_de_caso'] * 300
    with st.container(border=True):
        st.header('Mapa de contagios')
        st.map(df_contagios_departamento_mapa, latitude='latitud', longitude='longitud', size='size')


    df_contagios_departamento_mapa = df_join.groupby(by=['departamento_nom', 'latitud', 'longitud'], as_index=False).id_de_caso.count()
    df_contagios_departamento_mapa['size'] = df_contagios_departamento_mapa['id_de_caso'] * 300
    capas=pydeck.Layer(
        "ScatterplotLayer",
        data=df_contagios_departamento_mapa,
        get_position=["longitud", "latitud"],
        get_color="[255, 75, 75]",
        pickable=True,
        auto_highlight=True,
        get_radius="size",
    )

    vista_inicial=pydeck.ViewState(
        latitude=4,
        longitude=-74,
        zoom=4.5,
    )

    with st.container(border=True):
        st.header('Mapa de contagios')
        st.pydeck_chart(
            pydeck.Deck(
                layers=capas,
                map_style=None,
                initial_view_state=vista_inicial,
                tooltip={"text": "{departamento_nom}\nContagios: {id_de_caso}"}
            )
        )


with tab5:
    lista_departamento = df_join['departamento_nom'].sort_values().unique().tolist()
    lista_departamento.insert(0, 'Todos')
    option = st.selectbox('Seleccione el departamento', lista_departamento)
    if option == 'Todos':
        df_contagios_sexo = df_join.groupby(['sexo']).id_de_caso.count()
    else:
        df_contagios_sexo = df_join[df_join['departamento_nom'] == option].groupby(['sexo']).id_de_caso.count()
    fig, ax = plt.subplots()
    ax.pie(df_contagios_sexo, labels=df_contagios_sexo.index ,autopct='%1.1f%%')
    with st.container(border=True):
        st.header('Contagios por Sexo')
        st.pyplot(fig)
        


with tab6:
    fig, ax = plt.subplots()
    ax.hist(df_join['edad'])
    with st.container(border=True):
        st.header('Histograma por edades')
        st.pyplot(fig)

