FROM continuumio/miniconda3

WORKDIR /app/

RUN pip install --upgrade pip
RUN pip install streamlit scikit-learn pandas numpy seaborn requests matplotlib
RUN pip install streamlit-option-menu

COPY ./app/

ENV

CMD uvicorn app:app.py --reload &
CMD streamlit dashboard.py
