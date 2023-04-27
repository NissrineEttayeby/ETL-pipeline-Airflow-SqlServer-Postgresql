import time
from datetime import datetime
from airflow.models.dag import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from sqlalchemy import create_engine

#extract tasks

@task()
def get_src_tables():
    hook = MsSqlHook(mssql_conn_id="sqlserver")
    sql = """select  t.name as table_name  
     from sys.tables t where t.name in ('DimProduct','DimProductSubcategory','DimProductCategory')"""
    df = hook.get_pandas_df(sql)
    print(df)
    tbl_dict = df.to_dict('dict')
    return tbl_dict

@task()
def load_src_data(tbl_dict: dict):
    conn = PostgresHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    all_tbl_name = []
    start_time = time.time()
    for k, v in tbl_dict['table_name'].items():
        all_tbl_name.append(v)
        rows_imported = 0
        sql = f'select * FROM {v}'
        hook = MsSqlHook(mssql_conn_id="sqlserver")
        df = hook.get_pandas_df(sql)
        print(f'importing rows {rows_imported} to {rows_imported + len(df)}... for table {v} ')
        df.to_sql(f'src_{v}', engine, if_exists='replace', index=False)
        rows_imported += len(df)
        print(f'Done. {str(round(time.time() - start_time, 2))} total seconds elapsed')
    print("Data imported successful")
    return all_tbl_name

#Transformation tasks

@task()
def transform_srcProduct():
    conn = PostgresHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pdf = pd.read_sql_query('SELECT * FROM public."src_DimProduct" ', engine)
    # Drop columns
    revised = pdf[['ProductKey', 'ProductAlternateKey', 'ProductSubcategoryKey','WeightUnitMeasureCode', 'SizeUnitMeasureCode', 'EnglishProductName',
                   'StandardCost','FinishedGoodsFlag', 'Color', 'SafetyStockLevel', 'ReorderPoint','ListPrice', 'Size', 'SizeRange', 'Weight',
                   'DaysToManufacture','ProductLine', 'DealerPrice', 'Class', 'Style', 'ModelName', 'EnglishDescription', 'StartDate','EndDate', 'Status']]
    # Replace null values
    revised['WeightUnitMeasureCode'].fillna('0', inplace=True)
    revised['ProductSubcategoryKey'].fillna('0', inplace=True)
    revised['SizeUnitMeasureCode'].fillna('0', inplace=True)
    revised['StandardCost'].fillna('0', inplace=True)
    revised['ListPrice'].fillna('0', inplace=True)
    revised['ProductLine'].fillna('NA', inplace=True)
    revised['Class'].fillna('NA', inplace=True)
    revised['Style'].fillna('NA', inplace=True)
    revised['Size'].fillna('NA', inplace=True)
    revised['ModelName'].fillna('NA', inplace=True)
    revised['EnglishDescription'].fillna('NA', inplace=True)
    revised['DealerPrice'].fillna('0', inplace=True)
    revised['Weight'].fillna('0', inplace=True)
    # Rename columns
    revised = revised.rename(columns={"EnglishDescription": "Description", "EnglishProductName":"ProductName"})
    revised.to_sql(f'stg_DimProduct', engine, if_exists='replace', index=False)
    return {"table(s) processed ": "Data imported successful"}


@task()
def transform_srcProductSubcategory():
    conn = PostgresHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pdf = pd.read_sql_query('SELECT * FROM public."src_DimProductSubcategory" ', engine)
    # Drop columns
    revised = pdf[['ProductSubcategoryKey','EnglishProductSubcategoryName', 'ProductSubcategoryAlternateKey','EnglishProductSubcategoryName', 'ProductCategoryKey']]
    # Rename columns
    revised = revised.rename(columns={"EnglishProductSubcategoryName": "ProductSubcategoryName"})
    revised.to_sql(f'stg_DimProductSubcategory', engine, if_exists='replace', index=False)
    return {"table(s) processed ": "Data imported successful"}


@task()
def transform_srcProductCategory():
    conn = PostgresHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pdf = pd.read_sql_query('SELECT * FROM public."src_DimProductCategory" ', engine)
    # Drop columns
    revised = pdf[['ProductCategoryKey', 'ProductCategoryAlternateKey','EnglishProductCategoryName']]
    # Rename columns
    revised = revised.rename(columns={"EnglishProductCategoryName": "ProductCategoryName"})
    revised.to_sql(f'stg_DimProductCategory', engine, if_exists='replace', index=False)
    return {"table(s) processed ": "Data imported successful"}


#load task

@task()
def prdProduct_model():
    conn = PostgresHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pc = pd.read_sql_query('SELECT * FROM public."stg_DimProductCategory" ', engine)
    p = pd.read_sql_query('SELECT * FROM public."stg_DimProduct" ', engine)
    p['ProductSubcategoryKey'] = p.ProductSubcategoryKey.astype(float)
    p['ProductSubcategoryKey'] = p.ProductSubcategoryKey.astype(int)
    ps = pd.read_sql_query('SELECT * FROM public."stg_DimProductSubcategory" ', engine)
    #join all three
    merged = p.merge(ps, on='ProductSubcategoryKey').merge(pc, on='ProductCategoryKey')
    merged.to_sql(f'prd_DimProductCategory', engine, if_exists='replace', index=False)
    return {"table(s) processed ": "Data imported successful"}


#DAG

with DAG(dag_id="product_etl_dag",schedule="0 9 * * *", start_date=datetime(2023, 4, 27),catchup=False,  tags=["product_model"]) as dag:

    with TaskGroup("extract_dimProudcts_load", tooltip="Extract and load source data") as extract_load_src:
        src_product_tbls = get_src_tables()
        load_dimProducts = load_src_data(src_product_tbls)
        src_product_tbls >> load_dimProducts


    with TaskGroup("transform_src_product", tooltip="Transform and stage data") as transform_src_product:
        transform_srcProduct = transform_srcProduct()
        transform_srcProductSubcategory = transform_srcProductSubcategory()
        transform_srcProductCategory = transform_srcProductCategory()
        [transform_srcProduct, transform_srcProductSubcategory, transform_srcProductCategory]

    with TaskGroup("load_product_model", tooltip="Final Product model") as load_product_model:
        prd_Product_model = prdProduct_model()
        prd_Product_model

    extract_load_src >> transform_src_product >> load_product_model