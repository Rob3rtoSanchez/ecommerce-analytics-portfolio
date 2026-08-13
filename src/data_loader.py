"""
Módulo para cargar y unir las tablas del dataset Olist en un DataFrame maestro.
"""
import pandas as pd


def cargar_tablas(ruta_data='../data/'):
    """Carga las 9 tablas del dataset Olist desde archivos CSV."""
    tablas = {
        'customers': pd.read_csv(f'{ruta_data}olist_customers_dataset.csv'),
        'geolocation': pd.read_csv(f'{ruta_data}olist_geolocation_dataset.csv'),
        'order_items': pd.read_csv(f'{ruta_data}olist_order_items_dataset.csv'),
        'payments': pd.read_csv(f'{ruta_data}olist_order_payments_dataset.csv'),
        'reviews': pd.read_csv(f'{ruta_data}olist_order_reviews_dataset.csv'),
        'orders': pd.read_csv(f'{ruta_data}olist_orders_dataset.csv'),
        'products': pd.read_csv(f'{ruta_data}olist_products_dataset.csv'),
        'sellers': pd.read_csv(f'{ruta_data}olist_sellers_dataset.csv'),
        'category_translation': pd.read_csv(f'{ruta_data}product_category_name_translation.csv'),
    }
    return tablas


def limpiar_products(products):
    """Imputa nulos en products según la estrategia definida en el EDA (notebook 01)."""
    products = products.copy()
    products['product_category_name'] = products['product_category_name'].fillna('sem_categoria')
    products['product_name_lenght'] = products['product_name_lenght'].fillna(0)
    products['product_description_lenght'] = products['product_description_lenght'].fillna(0)
    products['product_photos_qty'] = products['product_photos_qty'].fillna(0)

    for col in ['product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']:
        products[col] = products[col].fillna(products[col].median())

    return products


def construir_dataframe_maestro(ruta_data='../data/'):
    """Ejecuta el pipeline completo: carga, limpieza y merge de todas las tablas."""
    tablas = cargar_tablas(ruta_data)
    tablas['products'] = limpiar_products(tablas['products'])

    df = tablas['orders'].merge(tablas['order_items'], on='order_id', how='left')
    df = df.merge(tablas['products'], on='product_id', how='left')
    df = df.merge(tablas['customers'], on='customer_id', how='left')
    df = df.merge(tablas['sellers'], on='seller_id', how='left')
    df = df.merge(tablas['category_translation'], on='product_category_name', how='left')

    payments_agg = tablas['payments'].groupby('order_id').agg(
        payment_value_total=('payment_value', 'sum'),
        payment_type_principal=('payment_type', 'first'),
        payment_installments_max=('payment_installments', 'max')
    ).reset_index()
    df = df.merge(payments_agg, on='order_id', how='left')

    reviews_dedup = tablas['reviews'].drop_duplicates(subset='order_id', keep='first')
    df = df.merge(
        reviews_dedup[['order_id', 'review_score']],
        on='order_id',
        how='left'
    )

    return df