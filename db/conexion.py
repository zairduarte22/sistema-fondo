from sqlalchemy import create_engine, MetaData, Table, Integer, Column, String, ForeignKey, Enum, DECIMAL, Date
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd
import streamlit as st

# 1. Obtener las credenciales de la base de datos desde el archivo secrets.toml
DB_USER = st.secrets["DB_USER"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]
DB_HOST = st.secrets["DB_HOST"]
DB_PORT = st.secrets["DB_PORT"]
DB_NAME = st.secrets["DB_NAME"]

def motor():
    try:
        # 1. Conexión a la base de datos
        DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        print(f'Se produjo un error al conectar a la base de datos: {e}')

conexion = motor()

def consultas():
    Session = sessionmaker(bind=conexion)
    session = Session()
    return session

session = consultas()

# 2. Reflejar todas las tablas existentes
metadata = MetaData()
metadata.reflect(bind=conexion)  # Esto lee la estructura de la base de datos

Base = declarative_base()

# 3. Instanciar todas las tablas como objetos
# Tabla MIEMBROS
class Miembro(Base):
    __tablename__ = 'MIEMBROS'
    ID_MIEMBRO = Column(Integer, primary_key=True)
    RAZON_SOCIAL = Column(String(60), nullable=False)
    RIF = Column(String(15), nullable=False)
    ULTIMO_MES = Column(String(30))
    SALDO = Column(DECIMAL(10, 2), default=0.00)
    ESTADO = Column(String(10), default='SOLVENTE')

# Tabla INFORMACION_MIEMBRO
class InformacionMiembro(Base):
    __tablename__ = 'INFORMACION_MIEMBRO'
    ID_MIEMBRO = Column(Integer, ForeignKey('MIEMBROS.ID_MIEMBRO'), primary_key=True)
    NUM_TELEFONO = Column(String(20))
    REPRESENTANTE = Column(String(70))
    CI_REPRESENTANTE = Column(String(30))
    CORREO = Column(String(30))
    DIRECCION = Column(String(30))
    HACIENDA = Column(String(30))

# Tabla FACT_CUOTAS
class FactCuota(Base):
    __tablename__ = 'FACT_CUOTAS'
    ID_FACTURA = Column(Integer, primary_key=True, autoincrement=True)
    ID_MIEMBRO = Column(Integer, ForeignKey('MIEMBROS.ID_MIEMBRO'), nullable=False)
    FECHA = Column(Date, default='CURRENT_DATE')
    MONTO_BS = Column(DECIMAL(10, 2), nullable=False)
    MONTO_DIVISAS = Column(DECIMAL(10, 2), nullable=False)
    METODO_PAGO = Column(String(30), nullable=False)
    FACT_UGAVI = Column(Integer, unique=True)
    FACT_FONDO = Column(Integer, unique=True)
    MENSUALIDADES = Column(String(120), nullable=False)
    REFERENCIA = Column(String(30))
    ESTADO = Column(Enum('VIGENTE', 'ANULADA'), default='VIGENTE')

# Tabla SALDOS
class Saldo(Base):
    __tablename__ = 'SALDOS'
    ID_SALDO = Column(Integer, primary_key=True, autoincrement=True)
    ID_MIEMBRO = Column(Integer, ForeignKey('MIEMBROS.ID_MIEMBRO'), nullable=False)
    ID_FACTURA = Column(Integer, ForeignKey('FACT_CUOTAS.ID_FACTURA'))
    DESCRIPCION = Column(String(30), nullable=False)
    MONTO = Column(DECIMAL(10, 2), nullable=False)

# Tabla INGRESOS (antes VENTAS)
class Ingreso(Base):
    __tablename__ = 'INGRESOS'
    ID_INGRESO = Column(Integer, primary_key=True, autoincrement=True)
    ID_FACTURA = Column(Integer, ForeignKey('FACT_CUOTAS.ID_FACTURA'))
    FECHA = Column(Date, default='CURRENT_DATE')
    CUENTA_CONTABLE = Column(String(30))
    TIPO_INGRESO = Column(String(30))
    BENEFICIARIO = Column(String(30))
    METODO_PAGO = Column(String(30))
    DETALLE = Column(String(30))
    MONTO = Column(DECIMAL(10, 2))
    MONTO_DIVISAS = Column(DECIMAL(10, 2))
    REFERENCIA = Column(String(30))
    NUMERO_FACTURA = Column(String(30))
    NUMERO_CONTROL = Column(String(30))
    TITULAR = Column(String(30))

# Tabla EGRESOS (antes COMPRAS)
class Egreso(Base):
    __tablename__ = 'EGRESOS'
    ID_EGRESO = Column(Integer, primary_key=True, autoincrement=True)
    FECHA = Column(Date, default='CURRENT_DATE')
    CUENTA_CONTABLE = Column(String(30))
    TIPO_OPERACION = Column(String(100))
    BENEFICIARIO = Column(String(30))
    METODO_PAGO = Column(String(30))
    DETALLE = Column(String(30))
    MONTO = Column(DECIMAL(10, 2))
    MONTO_DIVISAS = Column(DECIMAL(10, 2))
    BASE_IMPONIBLE = Column(DECIMAL(10, 2))
    IVA = Column(DECIMAL(10, 2))
    REFERENCIA = Column(String(30))
    NUMERO_FACTURA = Column(String(30))
    NUMERO_CONTROL = Column(String(30))
    TITULAR = Column(String(30), default='FONDO DE UGAVI')

# Tabla CONCILIACION_BS
class ConciliacionBS(Base):
    __tablename__ = 'CONCILIACION_BS'
    ID_MOVIMIENTO = Column(Integer, primary_key=True, autoincrement=True)
    ID_INGRESOS = Column(Integer, ForeignKey('INGRESOS.ID_INGRESO'))
    ID_FACTURA = Column(Integer, ForeignKey('FACT_CUOTAS.ID_FACTURA'))
    ID_EGRESOS = Column(Integer, ForeignKey('EGRESOS.ID_EGRESO'))
    FECHA = Column(Date, default='CURRENT_DATE')
    CUENTA_CONTABLE = Column(String(30))
    TIPO_OPERACION = Column(String(30))
    REFERENCIA = Column(String(30))
    BENEFICIARIO = Column(String(30))
    DESCRIPCION = Column(String(30))
    INGRESO = Column(DECIMAL(10, 2))
    EGRESO = Column(DECIMAL(10, 2))

# Tabla CONCILIACION_DIVISAS
class ConciliacionDivisas(Base):
    __tablename__ = 'CONCILIACION_DIVISAS'
    ID_MOV_DIVISAS = Column(Integer, primary_key=True, autoincrement=True)
    ID_INGRESOS = Column(Integer, ForeignKey('INGRESOS.ID_INGRESO'))
    ID_FACTURA = Column(Integer, ForeignKey('FACT_CUOTAS.ID_FACTURA'))
    ID_EGRESOS = Column(Integer, ForeignKey('EGRESOS.ID_EGRESO'))
    FECHA = Column(Date, default='CURRENT_DATE')
    CUENTA_CONTABLE = Column(String(30))
    TIPO_OPERACION = Column(String(30))
    REFERENCIA = Column(String(30))
    BENEFICIARIO = Column(String(30))
    DESCRIPCION = Column(String(30))
    INGRESO = Column(DECIMAL(10, 2))
    EGRESO = Column(DECIMAL(10, 2))
    METODO_PAGO = Column(String(30))
    TITULAR = Column(String(30))


# FUNCION PARA OBTENER TODOS LOS DATOS DE UN TABLA
def obtener_df(x):
    try:
        query = session.query(x).statement
        df = pd.read_sql(query, session.bind)
        return df
    except Exception as e:
        session.rollback()
        st.error(f'Se ha producido un error al tratar de obtener los datos. Error: {e}')
        return None
    finally:
        session.close()

# FUNCION PARA OBTENER TODOS LOS DATOS DE DOS TABLAS USANDO EL JOIN
def obtener_df_join(x, y):
    try:
        query = session.query(x, y).join(y).statement
        df = pd.read_sql(query, session.bind)
        return df
    except Exception as e:
        session.rollback()
        st.error(f'Se ha producido un error al tratar de obtener los datos. Error: {e}')
        return None
    finally:
        session.close()