import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

basic_url = "https://drive.google.com/uc?export=download&id=1CSU9AMA3o-1j_3UFLGc2efCMs8MhR3ek"
basic = pd.read_csv(basic_url)