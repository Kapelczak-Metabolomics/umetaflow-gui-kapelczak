import streamlit as st
import numpy as np
from src.view import *
from src.constants import ERRORS
from streamlit_plotly_events import plotly_events

st.set_page_config(
    page_title="UmetaFlow",
    page_icon="resources/icon.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)


def content():
    with st.sidebar:
        st.image("resources/OpenMS.png", "powered by")
    st.title("View raw MS data")

    st.session_state.view_spectra_dict = get_spectra_dict(st.session_state["mzML_dfs"])

    c1, c2 = st.columns(2)
    c1.selectbox(
        "choose file", st.session_state.view_spectra_dict.keys(), key="view_file"
    )

    st.session_state.view_df_MS1, st.session_state.view_df_MS2 = get_dfs(
        st.session_state.view_spectra_dict, st.session_state.view_file
    )

    if not st.session_state.view_df_MS1.empty:
        st.markdown("### Peak Map and MS2 spectra")
        c1, c2 = st.columns(2)
        c1.number_input(
            "2D map intensity cutoff",
            1000,
            1000000000,
            5000,
            1000,
            key="cutoff",
        )
        if not st.session_state.view_df_MS2.empty:
            c2.markdown("##")
            c2.markdown("💡 Click anywhere to show the closest MS2 spectrum.")
        st.session_state.view_fig_map = plot_2D_map(
            st.session_state.view_df_MS1,
            st.session_state.view_df_MS2,
            st.session_state.cutoff,
        )
        # Determine RT and mz positions from clicks in the map to get closest MS2 spectrum
        if not st.session_state.view_df_MS2.empty:
            map_points = plotly_events(st.session_state.view_fig_map)
            if map_points:
                rt = map_points[0]["x"]
                prec_mz = map_points[0]["y"]
            else:
                rt = st.session_state.view_df_MS2.iloc[0, 2]
                prec_mz = st.session_state.view_df_MS2.iloc[0, 0]
            spec = st.session_state.view_df_MS2.loc[
                (
                    abs(st.session_state.view_df_MS2["RT"] - rt)
                    + abs(st.session_state.view_df_MS2["precursormz"] - prec_mz)
                ).idxmin(),
                :,
            ]
            plot_ms_spectrum(
                spec,
                f"MS2 spectrum @precursor m/z {round(spec['precursormz'], 4)} @RT {round(spec['RT'], 2)}",
                "#00CC96",
            )
        else:
            st.plotly_chart(st.session_state.view_fig_map, use_container_width=True)

        # BPC and MS1 spec
        st.markdown("### Base Peak Chromatogram (BPC)")
        st.markdown("💡 Click a point in the BPC to show the MS1 spectrum.")
        st.session_state.view_fig_bpc = plot_bpc(st.session_state.view_df_MS1)

        # Determine RT positions from clicks in BPC to show MS1 at this position
        bpc_points = plotly_events(st.session_state.view_fig_bpc)
        if bpc_points:
            st.session_state.view_MS1_RT = bpc_points[0]["x"]
        else:
            st.session_state.view_MS1_RT = st.session_state.view_df_MS1.loc[0, "RT"]

        spec = st.session_state.view_df_MS1.loc[
            st.session_state.view_df_MS1["RT"] == st.session_state.view_MS1_RT
        ].squeeze()

        plot_ms_spectrum(
            spec,
            f"MS1 spectrum @RT {spec['RT']}",
            "#EF553B",
        )


if __name__ == "__main__":
    try:
        content()
    except:
        st.warning(ERRORS["visualization"])
