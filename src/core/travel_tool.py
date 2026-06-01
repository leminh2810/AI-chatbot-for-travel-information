import pandas as pd
import json

class TravelTools:
    def __init__(self, csv_path="Data.csv"):
        try:
            self.df = pd.read_csv(csv_path)
            # Chuẩn hóa kiểu ngày tháng
            self.df['booking_date'] = pd.to_datetime(self.df['booking_date'])
            self.df['travel_date'] = pd.to_datetime(self.df['travel_date'])
        except Exception as e:
            print(f"Lỗi khi đọc file Data.csv: {e}")
            self.df = pd.DataFrame()

    def check_booking_status(self, booking_id: str) -> str:
        """
        Tra cứu trạng thái và thông tin chi tiết của một mã đơn đặt chỗ (booking_id).
        Tham số nhập vào:
        - booking_id (str): Mã booking bắt đầu bằng chữ 'B' kèm số (VD: 'B00001').
        """
        if self.df.empty: return "Cơ sở dữ liệu trống."
        res = self.df[self.df['booking_id'] == booking_id]
        if res.empty:
            return f"Không tìm thấy thông tin cho mã booking {booking_id}."
        return res.to_json(orient="records", force_ascii=False)

    def analyze_customer_history(self, customer_id: str) -> str:
        """
        Phân tích lịch sử du lịch của khách hàng dựa trên customer_id để xem hành vi, các điểm đến đã đi, tổng tiền và mức độ hài lòng.
        Tham số nhập vào:
        - customer_id (str): Mã khách hàng bắt đầu bằng chữ 'C' kèm số (VD: 'C0088').
        """
        if self.df.empty: return "Cơ sở dữ liệu trống."
        res = self.df[self.df['customer_id'] == customer_id]
        if res.empty:
            return f"Không tìm thấy dữ liệu cho mã khách hàng {customer_id}."
        
        total_trips = len(res)
        destinations = res['destination'].unique().tolist()
        total_spent = float(res['revenue_vnd'].sum())
        avg_satisfaction = float(res['satisfaction'].mean())
        
        analysis = {
            "customer_id": customer_id,
            "total_trips": total_trips,
            "destinations_visited": destinations,
            "total_revenue_vnd": total_spent,
            "average_satisfaction": round(avg_satisfaction, 2)
        }
        return json.dumps(analysis, ensure_ascii=False)

    def calculate_destination_revenue(self, destination: str) -> str:
        """
        Tính tổng doanh thu (revenue_vnd) và tổng số lượng khách (pax) đã tới một địa điểm du lịch cụ thể.
        Tham số nhập vào:
        - destination (str): Tên thành phố/địa điểm du lịch bằng tiếng Việt có dấu (VD: 'Huế', 'Phú Quốc', 'Hạ Long', 'TP.HCM').
        """
        if self.df.empty: return "Cơ sở dữ liệu trống."
        res = self.df[self.df['destination'].str.lower() == destination.lower()]
        if res.empty:
            return f"Không có dữ liệu doanh thu cho địa điểm: {destination}."
        
        total_revenue = float(res['revenue_vnd'].sum())
        total_pax = int(res['pax'].sum())
        completed_bookings = len(res[res['booking_status'] == 'Completed'])
        
        return json.dumps({
            "destination": destination,
            "total_revenue_vnd": total_revenue,
            "total_pax_served": total_pax,
            "completed_bookings_count": completed_bookings
        }, ensure_ascii=False)