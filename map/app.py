from flask import Flask, request, jsonify, render_template
import requests
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Google Maps APIキーを設定 (YOUR_GOOGLE_MAPS_API_KEYに置き換えてください)
GMAPS_API_KEY = 'API'

# 来店済み店舗を保存するファイル
VISITED_SHOPS_FILE = 'visited_shops.json'

# 来店済み店舗リストを読み込む
def load_visited_shops():
    try:
        with open(VISITED_SHOPS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# 来店済み店舗リストを保存する
def save_visited_shops(shops):
    with open(VISITED_SHOPS_FILE, 'w') as file:
        json.dump(shops, file)

# ホームページを表示するルート
@app.route('/')
def index():
    return render_template('index.html')

# ルート案内と近くの店舗を取得する関数
def get_route_and_shops(start_location, end_location, radius=50):
    visited_shops = load_visited_shops()
    try:
        origin_lat, origin_lng = start_location.split(',')
        destination_lat, destination_lng = end_location.split(',')
        
        # ルート案内の取得
        url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin_lat},{origin_lng}&destination={destination_lat},{destination_lng}&mode=driving&key={GMAPS_API_KEY}'
        response = requests.get(url)
        directions = response.json()
        
        if directions['status'] == 'OK':
            route = directions['routes'][0]['legs'][0]['steps']
            shops = []
            for step in route:
                lat = step['end_location']['lat']
                lng = step['end_location']['lng']

                # 店舗情報の取得 (language=jaを追加)
                shop_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=restaurant|cafe&language=ja&key={GMAPS_API_KEY}'
                shop_response = requests.get(shop_url)
                places = shop_response.json()

                if places['status'] == 'OK':
                    for place in places['results'][:3]:  # 各ポイントで3件取得
                        if place['place_id'] not in visited_shops:
                            shops.append({
                                'name': place['name'],  # 店名を日本語で取得
                                'address': place['vicinity'],  # 住所も日本語対応
                                'location': place['geometry']['location'],
                                'place_id': place['place_id']
                            })

            return shops
        else:
            return []
    except Exception as e:
        print(f"Error fetching route or nearby shops: {e}")
        return []

# 来店済み店舗の記録
@app.route('/visited-shop', methods=['POST'])
def visited_shop():
    place_id = request.form.get('place_id')
    if not place_id:
        return jsonify({"error": "place_id is required"}), 400

    visited_shops = load_visited_shops()
    if place_id not in visited_shops:
        visited_shops.append(place_id)
        save_visited_shops(visited_shops)

    return jsonify({"message": "Shop visit recorded successfully."})

# APIエンドポイント: ルート案内と店舗情報を提供
@app.route('/get-route', methods=['GET'])
def get_route_and_shops_api():
    start_location = request.args.get('start')
    end_location = request.args.get('end')

    if not start_location or not end_location:
        return jsonify({"error": "Both start and end locations are required"}), 400
    
    nearby_shops = get_route_and_shops(start_location, end_location)
    if not nearby_shops:
        return jsonify({"error": "Unable to get route or nearby shops"}), 500
    
    return jsonify(nearby_shops)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
