from streamlit.web import cli

if __name__=='__main__':
    cli._main_run_clExplicit(['app.py', 'local'], 'streamlit run')

    # we will create this function inside our streamlit framework
