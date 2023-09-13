#libraries
import pandas as pd
import polars as pl
import os

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error as mape
import pmdarima as pm

def read_some_file():
    file = input('Enter absolute path: ')

    file_name, file_type = os.path.splitext(file)

    #reading file and writing data to dataframe
    if file_type == '.csv':
        data = pd.read_csv(file)
        df = pd.DataFrame(data)

        return df
    elif file_type == '.parquet':
        data = pl.read_ipc(file)
        df = pd.DataFrame(data=data.to_pandas())

        return df

    return None

def train_and_test_split(df: pd.DataFrame, df_corr: pd.DataFrame, col_name: str):
    n_values = int(input('Enter a number of values to be predicted: '))

    mas = []
    for col in df.columns:
        if df_corr[col][col_name] < 0.35:
            mas.append(col)

    real_df = df.drop(mas, axis=1)

    #spliting dataframe to test and train
    train = real_df[:(len(real_df) - n_values)]
    test = real_df[(len(real_df) - n_values):]

    return train, test, n_values, real_df

def test_x_model_prediction(train: pd.DataFrame, test: pd.DataFrame,
                            n_values: int, col_name: str, real_df: pd.DataFrame):
    # devide train to x and y
    train_x = train.drop(col_name, axis=1)

    # devide test to x and y
    test_x = test.drop(col_name, axis=1)

    df_pred = pd.DataFrame()

    for col in train_x.columns:
        model = pm.auto_arima(train_x[col])
        prediction = model.predict(n_periods=n_values)

        if mape(test_x[col], prediction) <= 0.9:
            model2 = pm.auto_arima(real_df[col])
            prediction2 = model2.predict(n_periods=n_values)
            prediction2 = pd.Series(prediction2)
            df_pred = pd.DataFrame(prediction2)
    return df_pred

def test_y_model(df: pd.DataFrame, df_corr: pd.DataFrame):
    # choosing column to be predicted
    print(df.columns)
    col_name = input(f'choose column to be predicted: ')

    train, test, n_values, real_df = train_and_test_split(df, df_corr, col_name)

    if train.shape[1] == 1:
        #building an arima model and making a prediction for one variable
        model = pm.auto_arima(train[col_name])
        prediction = model.predict(n_periods=len(test))

        print(f'ARIMA mape: {mape(test[col_name], prediction)}')
        model_final = 'AR'

        df_pred = 0
    else:
        # building a linear regression model and making a prediction
        model = LinearRegression()
        model.fit(train.drop(col_name, axis=1), train[col_name])
        prediction = model.predict(test.drop(col_name, axis=1))

        mapa = mape(test[col_name], prediction)

        # building an arima model and making a prediction
        model2 = pm.auto_arima(train[col_name], train.drop(col_name, axis=1))
        prediction2 = model2.predict(n_periods=len(test), X=test.drop(col_name, axis=1))

        mapa2 = mape(test[col_name], prediction2)

        #deciding which model is better using mean_absolute_percentage_error
        if mapa < mapa2:
            print(f'LinearRegression mape: {mapa}')
            model_final = 'LR'
        else:
            print(f'ARIMA mape: {mapa2}')
            model_final = 'AR'

        df_pred = test_x_model_prediction(train, test, n_values, col_name, real_df)

    return model_final, col_name, n_values, real_df, df_pred

def building_model(model_final: str, df: pd.DataFrame,
                   col_name: str, n_values: int, real_df: pd.DataFrame, df_pred: pd.DataFrame):
    if model_final == 'LR':
        model_y = LinearRegression()
        model_y.fit(real_df.drop(col_name, axis=1), real_df[col_name])
        prediction_y = model_y.predict(df_pred)

        return prediction_y
    elif model_final == 'AR':
        if real_df.shape[1] == 1:
            model = pm.auto_arima(real_df[col_name])
            prediction = model.predict(n_periods=n_values)

            return prediction
        else:
            model = pm.auto_arima(real_df[col_name], real_df.drop(col_name, axis=1))
            prediction = model.predict(n_periods=n_values, X=df_pred)

            return prediction

def main():
     df = read_some_file()

     #making df of correlations
     df_corr = df.corr()

     model_final, col_name, n_values, real_df, df_pred = test_y_model(df, df_corr)
     prediction = building_model(model_final, df, col_name, n_values, real_df, df_pred)

     print(prediction)

if __name__ == '__main__':
    main()