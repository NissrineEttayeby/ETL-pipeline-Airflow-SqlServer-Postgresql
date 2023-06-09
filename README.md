![image](https://user-images.githubusercontent.com/108592629/234983588-d97ae24d-93fd-4dd9-bcbb-561d27d145b4.png)

# ETL pipeline

is a set of processes which extract the data from an input source, transform the data and loading it into an output destination such as datamart, database and data warehouse for analysis, reporting and data synchronization.



![image](https://user-images.githubusercontent.com/108592629/235002938-e5e3a900-79a4-41ca-9542-da2b2b1f425d.png)



### Extract
In this stage, data is extracted from sql server database.

### Transform
The second step is to transform the data into a format that is used by Postgresql. In this stage, we convert the data into a form which is used for standardized processing. 

### Load
This is the final phase of the ETL process. Here, the information is available in consistent format. Now we can obtain any specific piece of data. And we can use it for different applications.


# Apache Airflow
 is an open-source platform for developing, scheduling, and monitoring batch-oriented workflows.

## Components of Airflow
* DAGs
* Tasks
* The operators
* Hooks
* Plugins
* Connections

> 
![33](https://user-images.githubusercontent.com/108592629/235002894-2394500d-d2c8-4baa-bb0f-00ca3d257bdf.png)




# Microsoft Sql server
is a relational database management system (RDBMS) used as a source from where we extract the data using python scripts and airflow.

# PostgreSQL 
is a powerful, open source object-relational database system ,its able to be used for both OLTP and OLAP. And it is used as the datawarehouse or the target where we load the data extracted from Sql Server in this project .

[Apache Airflow](https://airflow.apache.org/) 

[Sql Server](https://www.microsoft.com/en-us/sql-server/) 

[Postgresql](https://www.postgresql.org/) 


