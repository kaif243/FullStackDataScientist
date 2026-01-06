import os
import requests
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

from sklearn.svm import SVC
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


# logger
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# Session state initilization
if "cleaned_saved" not in st.session_state:
    st.session_state.cleaned_saved = False

# Folder Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)

log("Application started")
log(f"RAW_DIR = {RAW_DIR}")
log(f"CLEANED_DIR = {CLEANED_DIR}")

# Page Configuration
st.set_page_config("END-TO-END SVM", layout="wide")
st.title("END-TO-END SVM Platform")

# Sidbar : Model settings
st.sidebar.header("SVM Settings")
kernel = st.sidebar.selectbox("kernel", ["linear", "poly", "rbf", "sigmoid"])
C = st.sidebar.slider("C (Regularization)", 0.01, 10.0, 1.0)
gama = st.sidebar.selectbox("Gama", ["scale", "auto"])

log(f"SVM settings ----> kernel ={kernel}, C={C}, gama={gama}")

# Step 1: Data Ingestion
st.header("step 1: Data Ingestion")
log("Step 1: Data Ingestion Started")

options = st.radio("Choose data source", ["Download Dataset", "Upload CSV"])

df = None
raw_path = None
if options == "Download Dataset":
    if st.button("Download Iris Dataset"):
        log("Downloading Iris Dataset")
        url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
        response = requests.get(url)
        raw_path = os.path.join(RAW_DIR, "iris.csv")
        with open(raw_path, "wb") as f:
            f.write(response.content)

        df = pd.read_csv(raw_path)
        st.success("Dataset downloaded successfully")
        log(f"Iris Dataset saved at {raw_path} ")

if options == "Upload CSV":
    upload_file = st.file_uploader("Upload CSV File", type=["csv"])
    if upload_file:
        raw_path = os.path.join(RAW_DIR, upload_file.name)
        with open(raw_path, "wb") as f:
            f.write(upload_file.getbuffer())
        df = pd.read_csv(raw_path)
        st.success("File uploaded successfully")
        log(f"Uploaded file saved at {raw_path} ")


# Step 2: EDA

if df is not None:
    st.header("Step 2: EDA")
    log("Step 2: EDA Started")

    st.dataframe(df.head())
    st.write("Shape", df.shape)
    st.write("Missing values", df.isnull().sum())

    fig, ax = plt.subplots()
    sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)

    log("EDA completed")


# Step 3: Data Cleaning
if df is not None:
    st.header("Step 3: Data Cleaning")
    strategy = st.selectbox("Missing value Strategy", ["Mean", "Median", "Drop Rows"])
    df_clean = df.copy()
    if strategy == "Drop Rows":
        df_clean = df_clean.dropna()
    else:
        for col in df_clean.select_dtypes(include=[np.number]).columns:
            if strategy == "Mean":
                df_clean[col].fillna(df_clean[col].mean(), inplace=True)
            else:
                df_clean[col].fillna(df_clean[col].median(), inplace=True)
    st.session_state.df_clean = df_clean
    st.success("Data Cleaning Completed")
else:
    st.info("Please complete Step 1(Data Ingestion) first...")


# Step 4: Save the cleaned data
if st.button("Save Cleaned Data"):
    if st.session_state.df_clean is None:
        st.error("No cleaned data found. Please complete Step 3 first....")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_filename = f"cleaned_dataset_{timestamp}.csv"
        clean_path = os.path.join(CLEANED_DIR, cleaned_filename)

        st.session_state.df_clean.to_csv(clean_path, index=False)
        st.success("Cleaned dataset saved")
        st.info(f"Saved at:{clean_path}")
        log(f"Cleaned dataset saved at {clean_path}")


# Step 5: Load cleaned Dataset
st.header("Step 5: Load Cleaned Dataset")
cleaned_files = os.listdir(CLEANED_DIR)
if not cleaned_files:
    st.warning("No cleaned dataset found. Please save one in Step 4....")
    log("No cleaned dataset available")
else:
    selected = st.selectbox("Select Cleaned Dataset", cleaned_files)
    df_model = pd.read_csv(os.path.join(CLEANED_DIR, selected))
    st.success(f"Loaded dataset: {selected}")
    log(f"Loaded cleaned dataset: {selected}")

    st.dataframe(df_model.head())


# Step 6: Train SVM
st.header("Step 6: Train SVM ")
log("Step 6: Started SVM Training")

target = st.selectbox("Select Target Column", df_model.columns)
y = df_model[target]

if y.dtype == "object":
    le = LabelEncoder()
    y = le.fit_transform(y)
    log("Target Column encoded")

# Select numeric features only
x = df_model.drop(columns=[target])
x = x.select_dtypes(include=[np.number])

if x.empty:
    st.error("No numeric features available for training.")
    st.stop()

# Scale features
scaler = StandardScaler()
x = scaler.fit_transform(x)
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.25, random_state=40
)
model = SVC(kernel=kernel, C=C, gamma=gama)
model.fit(x_train, y_train)

# Evaluate
y_pred = model.predict(x_test)
acc = accuracy_score(y_test, y_pred)
st.success(f"Accuracy: {acc :.2f}")
log(f"SVM trained Successfully | Accuracy = {acc:.2f}")


cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots()
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
st.pyplot(fig)