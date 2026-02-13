
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
    # 1. Obtener Usuario y Meta
    user = current_app.db.users.find_one({'_id': ObjectId(session['user_id'])})
    profile = user.get('profile', {})
    weight_goal = profile.get('weight_goal')  # Meta

    # 2. Filtros de Fecha
    time_filter = request.args.get('filter', '1m')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = {'user_id': session['user_id']}
    now = datetime.now()

    if time_filter == '1m':
        query['recorded_date'] = {'$gte': now - timedelta(days=30)}
    elif time_filter == '3m':
        query['recorded_date'] = {'$gte': now - timedelta(days=90)}
    elif time_filter == 'custom' and start_date_str:
        try:
            s = datetime.strptime(start_date_str, '%Y-%m-%d')
            e = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else now
            query['recorded_date'] = {'$gte': s, '$lte': e.replace(hour=23, minute=59)}
        except:
            pass

    # 3. Obtener Datos (Ordenados por fecha antigua -> nueva)
    data = list(current_app.db.weight_entries.find(query).sort('recorded_date', 1))

    labels = []
    weights = []

    for entry in data:
        # Formato corto para el eje X (ahorra espacio)
        labels.append(entry['recorded_date'].strftime('%d/%m'))
        weights.append(entry['weight'])

    # 4. CÁLCULO DE TENDENCIA (Basado en Índices para línea recta visual)
    trendline = []
    if len(weights) > 1:
        # Usamos índices simples (0, 1, 2...) como eje X
        n = len(weights)
        x_indices = list(range(n))

        sum_x = sum(x_indices)
        sum_y = sum(weights)
        sum_xy = sum(x * y for x, y in zip(x_indices, weights))
        sum_xx = sum(x * x for x in x_indices)

        # Pendiente (m) y punto de corte (b)
        try:
            m = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
            b = (sum_y - m * sum_x) / n

            # Generar puntos de la línea
            for x in x_indices:
                val = m * x + b
                trendline.append(round(val, 2))
        except ZeroDivisionError:
            trendline = []

    return jsonify({
        'labels': labels,
        'data': weights,
        'trendline': trendline,
        'goal': weight_goal,  # Enviamos la meta
        'show_trend': len(trendline) > 0
    })