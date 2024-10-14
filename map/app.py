from flask import Flask, request, jsonify, render_template
import requests
from flask_cors import CORS

# Flaskアプリケーションの初期化
app = Flask(__name__)

# CORSを有効にする。これでフロントエンドからのリクエストを許可します。
CORS(app)

# Google Maps APIキーを設定 (YOUR_GOOGLE_MAPS_API_KEYに置き換えてください)
GMAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'

# ホームページを表示するルート
@app.route('/')
def index():
    return render_template('index.html')

# ルート案内を取得する関数
def get_route(start_location, end_location):
    try:
        origin_lat, origin_lng = start_location.split(',')
        destination_lat, destination_lng = end_location.split(',')
        
        url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin_lat},{origin_lng}&destination={destination_lat},{destination_lng}&mode=driving&key={GMAPS_API_KEY}'
        response = requests.get(url)
        directions = response.json()
        
        if directions['status'] == 'OK':
            route = directions['routes'][0]['legs'][0]['steps']
            return [step['end_location'] for step in route]
        else:
            return []
    except Exception as e:
        print(f"Error fetching route: {e}")
        return []

# ルート近くの店舗を検索する関数
def find_nearby_shops(locations, radius=30):
    shops = []
    for location in locations:
        lat = location['lat']
        lng = location['lng']
        try:
            url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=restaurant|cafe|convenience_store&key={GMAPS_API_KEY}'
            response = requests.get(url)
            places = response.json()
            
            if places['status'] == 'OK':
                for place in places['results'][:3]:  # 3件のみ取得
                    shops.append({
                        'name': place['name'],
                        'address': place['vicinity'],
                        'location': place['geometry']['location']
                    })
        except Exception as e:
            print(f"Error fetching nearby shops: {e}")
    return shops

# ルートと近くのお店を返すAPIエンドポイント
@app.route('/get-route', methods=['GET'])
def get_route_and_shops():
    start_location = request.args.get('start')  # 出発地（緯度,経度）
    end_location = request.args.get('end')  # 目的地（緯度,経度）

    if not start_location or not end_location:
        return jsonify({"error": "Both start and end locations are required"}), 400
    
    # 1. ルート案内を取得
    route_locations = get_route(start_location, end_location)
    if not route_locations:
        return jsonify({"error": "Unable to get route"}), 500
    
    # 2. ルート上の店舗を検索
    nearby_shops = find_nearby_shops(route_locations)
    
    return jsonify(nearby_shops)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Flaskを5001ポートで実行
