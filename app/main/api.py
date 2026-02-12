import pymongo
from flask import jsonify, request, session, current_app
from app.main import main_bp
from app.decorators import login_required
from bson.objectid import ObjectId
from datetime import datetime, timedelta


# Función auxiliar para calcular tendencia (Regresión Lineal: y = mx + b)
def calculate_trendline(data):
    if len(data) < 2:
        return []

    # Convertimos fechas a timestamps numéricos para el cálculo matemático
    x = [d['recorded_date'].timestamp() for d in data]
    y = [d['weight'] for d in data]

    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_xx = sum(xi ** 2 for xi in x)

    denominator = (n * sum_xx - sum_x ** 2)
    if denominator == 0: return []

    m = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - m * sum_x) / n

    # Generamos los puntos de la línea (solo inicio y fin para dibujar la recta)
    start_point = {'x': data[0]['recorded_date'].strftime('%Y-%m-%d'), 'y': m * x[0] + b}
    end_point = {'x': data[-1]['recorded_date'].strftime('%Y-%m-%d'), 'y': m * x[-1] + b}

    return [start_point, end_point]


@main_bp.route('/api/chart-data')
@login_required
def get_chart_data():
    user_id = session['user_id']
    filter_type = request.args.get('filter', '1m')  # '1m', 'all', 'custom'
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = {'user_id': user_id}

    # Lógica de Filtrado
    if filter_type == '1m':
        last_month = datetime.now() - timedelta(days=30)
        query['recorded_date'] = {'$gte': last_month}
    elif filter_type == 'custom' and start_date_str:
        try:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
            # Si hay fecha fin la usamos, si no, hasta hoy
            end = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.now()
            query['recorded_date'] = {'$gte': start, '$lte': end}
        except ValueError:
            pass  # Si falla el formato, devuelve todo o maneja error
    # Si es 'all', no agregamos filtro de fecha, trae todo.

    # Consulta a BD (Orden Ascendente para el gráfico: antiguo -> nuevo)
    cursor = current_app.db.weight_entries.find(query).sort('recorded_date', pymongo.ASCENDING)
    entries = list(cursor)

    if not entries:
        return jsonify({'labels': [], 'data': [], 'trendline': []})

    # Preparar datos para Chart.js
    labels = [e['recorded_date'].strftime('%Y-%m-%d') for e in entries]
    weights = [e['weight'] for e in entries]

    trendline_data = []
    # Solo calculamos tendencia si el usuario pide ver TODO el historial
    if filter_type == 'all':
        trendline_data = calculate_trendline(entries)

    return jsonify({
        'labels': labels,
        'data': weights,
        'trendline': trendline_data,  # Será una lista vacía si no es 'all'
        'show_trend': filter_type == 'all'
    })