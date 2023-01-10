import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
import numpy as np
import shutil
from src.helpers import Helper
from src.plotting import Plot
from src.gnps import *
from src.dataframes import DataFrames
from pathlib import Path

st.set_page_config(layout="wide")

results_dir = "results_extractchroms"
if not os.path.exists(results_dir):
    os.mkdir(results_dir)
# set all other viewing states to False
st.session_state.viewing_untargeted = False
# set extract specific session states
if "viewing_extract" not in st.session_state:
    st.session_state.viewing_extract = False
if "mzML_files_extract" not in st.session_state:
    st.session_state.mzML_files_extract = set()
if "masses_text_field" not in st.session_state:
    st.session_state.masses_text_field = "222.0972=GlcNAc\n294.1183=MurNAc"
with st.sidebar:
    with st.expander("info", expanded=True):
        st.markdown("""
Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
Download the results of selected samples and chromatograms as `tsv` or `xlsx` files.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc` or add RT limits with a further equal sign e.g. `222.0972=GlcNAc=2.4-2.6`. The specified time unit will be used for the RT limits. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as a summary with all samples and EICs AUC values as well as the chromatograms as one graph per sample. Choose the samples and chromatograms to display.
""")

st.title("Extracted Ion Chromatograms (EIC/XIC)")
col1, col2 = st.columns(2)
masses_input = col1.text_area("masses", st.session_state.masses_text_field,
            help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.",
            height=250)
unit = col2.radio("mass tolerance unit", ["ppm", "Da"])
if unit == "ppm":
    tolerance = col2.number_input("mass tolerance", 1, 100, 10)
elif unit == "Da":
    tolerance = col2.number_input("mass tolerance", 0.01, 10.0, 0.02)
time_unit = col2.radio("time unit", ["seconds", "minutes"])

col1, col2, col3= st.columns(3)
col2.markdown("##")
run_button = col2.button("**Extract Chromatograms!**")

st.markdown("***")
mzML_dir = "mzML_files"
if run_button and any(Path(mzML_dir).iterdir()):

    Helper().reset_directory(results_dir)

    # make a zip file with tables in tsv format
    tsv_dir = os.path.join(results_dir, "tsv-tables")
    Helper().reset_directory(tsv_dir)

    masses = []
    names = []
    times = []
    for line in [line for line in masses_input.split('\n') if line != '']:
        if len(line.split("=")) == 3:
            mass, name, time = line.split("=")
        elif len(line.split("=")) == 2:
            mass, name = line.split("=")
            time = "all"
        else:
            mass = line
            name = ''
            time = "all"
        masses.append(float(mass.strip()))
        names.append(name.strip())
        time_factor = 1.0
        if time_unit == "minutes":
            time_factor = 60.0
        if "-" in time:
            times.append([float(time.split("-")[0].strip())*time_factor, float(time.split("-")[1].strip())*time_factor])
        else:
            times.append([0,0])
    for file in Path(mzML_dir).glob("*.mzML"):
        with st.spinner("Extracting from: " + str(file)):
            exp = MSExperiment()
            MzMLFile().load(str(file), exp)
            df = pd.DataFrame()
            # get BPC always
            time = []
            intensity = []
            for spec in exp:
                _, intensities = spec.get_peaks()
                rt = spec.getRT()
                if time_unit == "minutes":
                    rt = rt/60
                time.append(rt)
                i = int(max(intensities))
                intensity.append(i)
            df["time"] = time
            df["BPC"] = intensity
            # get EICs
            for mass, name, time in zip(masses, names, times):
                intensity = []
                for spec in exp:
                    if (time == [0,0]) or (time[0] < spec.getRT() and time[1] > spec.getRT()):
                        _, intensities = spec.get_peaks()
                        if unit == "Da":
                            index_highest_peak_within_window = spec.findHighestInWindow(mass, tolerance, tolerance)
                        else:
                            index_highest_peak_within_window = spec.findHighestInWindow(mass,float((tolerance/1000000)*mass),float((tolerance/1000000)*mass))
                        if index_highest_peak_within_window > -1:
                            intensity.append(int(spec[index_highest_peak_within_window].getIntensity()))
                        else:
                            intensity.append(0)
                    else:
                        intensity.append(0)
                df[str(mass)+"_"+name] = intensity
        df.to_feather(os.path.join(results_dir, os.path.basename(file)[:-5]+".ftr"))
        df.to_csv(os.path.join(tsv_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)
    shutil.make_archive(os.path.join(results_dir, "chromatograms"), 'zip', tsv_dir)
    shutil.rmtree(tsv_dir)

if any(Path(results_dir).iterdir()):
    st.markdown("there are some results")
