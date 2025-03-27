# Sistema de Inventario de Huevos

Este es un sistema web para gestionar el inventario de huevos, incluyendo entradas, salidas, clientes, repartidores y pedidos.

## Características

- Gestión de inventario de diferentes tipos de huevos
- Registro de movimientos (entradas, salidas, devoluciones)
- Gestión de clientes
- Gestión de repartidores
- Registro de pedidos
- Validación de stock disponible
- Historial de movimientos y pedidos

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio o descargar los archivos
2. Crear un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Iniciar la aplicación:
   ```bash
   python app.py
   ```
2. Abrir el navegador y acceder a `http://localhost:5000`

## Estructura de la Aplicación

La aplicación está organizada en las siguientes secciones:

1. **Inventario**: Muestra el stock actual de cada producto y permite registrar movimientos
2. **Movimientos**: Muestra el historial de todos los movimientos realizados
3. **Clientes**: Permite registrar nuevos clientes y ver la lista de clientes
4. **Repartidores**: Permite registrar nuevos repartidores y ver la lista de repartidores
5. **Pedidos**: Permite registrar nuevos pedidos y ver el historial de pedidos

## Base de Datos

La aplicación utiliza SQLite como base de datos, que se crea automáticamente al iniciar la aplicación por primera vez. Los productos iniciales se crean automáticamente:

- huevo rojo200
- huevo blanco sucio
- huevo blanco200
- huevo rojo360
- huevo rojito
- huevo pewe 