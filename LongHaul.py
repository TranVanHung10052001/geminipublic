import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px

# --- 1. CẤU HÌNH & TỐI ƯU LOAD DỮ LIỆU ---
st.set_page_config(layout="wide", page_title="Ahamove Dashboard")

@st.cache_data
def load_data():
    path = r'C:\Users\Admin\Downloads\LongHaul\Longhaul.csv'
    # Thêm low_memory=False để xử lý lỗi DtypeWarning
    df = pd.read_csv(path, encoding='utf-8-sig', low_memory=False)
    
    # Ép kiểu dữ liệu để tính toán ổn định
    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    df['hour_time'] = pd.to_numeric(df['hour_time'], errors='coerce').fillna(0).astype(int)
    
    # Xử lý total_fee: bỏ dấu phẩy, ép về số
    if df['total_fee'].dtype == 'object':
        df['total_fee'] = df['total_fee'].str.replace(',', '').astype(float)
    
    # Loại bỏ tọa độ trống
    df = df.dropna(subset=['pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng'])
    return df

df = load_data()

# --- 2. SIDEBAR: BỘ LỌC ĐẦY ĐỦ (CÓ CHỌN TẤT CẢ) ---
st.sidebar.title("🎮 Bộ lọc dữ liệu")

def create_multiselect(label, column, key_prefix):
    options = sorted([str(x) for x in df[column].unique()])
    container = st.sidebar.container()
    select_all = container.checkbox(f"Chọn tất cả {label}", value=True, key=f"all_{key_prefix}")
    
    if select_all:
        return container.multiselect(label, options, default=options, key=key_prefix)
    else:
        return container.multiselect(label, options, default=[], key=key_prefix)

# Khai báo các filter
city_ids = create_multiselect("Thành phố (city_id)", "city_id", "city")
statuses = create_multiselect("Trạng thái (status)", "status", "status")
services = create_multiselect("Dịch vụ (service_id)", "service_id", "service")
distances = create_multiselect("Khoảng cách (order_distance)", "order_distance", "dist")
cancel_types = create_multiselect("Loại hủy (Cancel_type)", "Cancel_type", "cancel")
hours = st.sidebar.slider("Khung giờ", 0, 23, (0, 23))

# --- 3. LOGIC LỌC DỮ LIỆU ---
df_filtered = df[
    (df['city_id'].astype(str).isin(city_ids)) &
    (df['status'].astype(str).isin(statuses)) &
    (df['service_id'].astype(str).isin(services)) &
    (df['order_distance'].astype(str).isin(distances)) &
    (df['Cancel_type'].astype(str).isin(cancel_types)) &
    (df['hour_time'] >= hours[0]) &
    (df['hour_time'] <= hours[1])
]

# --- 4. HIỂN THỊ CÁC THẺ CHỈ SỐ (KPI CARDS) ---
st.title("🚀 Ahamove Long Haul Operations")

# Tính toán các chỉ số
total_count = len(df_filtered)
completed_df = df_filtered[df_filtered['status'] == 'COMPLETED']
cancelled_df = df_filtered[df_filtered['status'] == 'CANCELLED']

fr = (len(completed_df) / total_count * 100) if total_count > 0 else 0
cr = (len(cancelled_df) / total_count * 100) if total_count > 0 else 0
total_gmv = completed_df['total_fee'].sum()
lost_gmv = cancelled_df['total_fee'].sum()

# Hiển thị hàng thẻ chỉ số
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Tổng đơn hàng", f"{total_count:,}")
c2.metric("Tỷ lệ Hoàn thành", f"{fr:.1f}%")
c3.metric("Tỷ lệ Hủy đơn", f"{cr:.1f}%", delta=f"{cr:.1f}%", delta_color="inverse")
c4.metric("GMV Thành công", f"{total_gmv/1e6:.1f}M")
c5.metric("GMV Tổn thất (Hủy)", f"{lost_gmv/1e6:.1f}M")

st.markdown("---")

# --- 5. BẢN ĐỒ VÀ BIỂU ĐỒ ---
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("📍 Bản đồ mật độ đơn hàng")
    view_type = st.radio("Dữ liệu:", ["Pickup", "Dropoff"], horizontal=True)
    
    if not df_filtered.empty:
        lat_col = 'pickup_lat' if view_type == "Pickup" else 'dropoff_lat'
        lng_col = 'pickup_lng' if view_type == "Pickup" else 'dropoff_lng'
        
        # Bản đồ nền trắng chuẩn
        m = folium.Map(location=[df_filtered[lat_col].mean(), df_filtered[lng_col].mean()], 
                       zoom_start=11, tiles='OpenStreetMap')
        
        heat_data = df_filtered[[lat_col, lng_col]].values.tolist()
        HeatMap(heat_data, radius=12, blur=10, min_opacity=0.4).add_to(m)
        st_folium(m, width="100%", height=500, key="map_stable")
    else:
        st.warning("Không có dữ liệu để hiển thị bản đồ.")

with col_right:
    st.subheader("📊 Phân tích trạng thái")
    # Biểu đồ trạng thái đơn
    fig_status = px.pie(df_filtered, names='status', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Biểu đồ lý do hủy chính
    if len(cancelled_df) > 0:
        cancel_reasons = cancelled_df['Final_Main_Reason'].value_counts().reset_index()
        fig_cancel = px.bar(cancel_reasons, x='Final_Main_Reason', y='count', 
                            title="Lý do hủy đơn", color_discrete_sequence=['#ef553b'])
        st.plotly_chart(fig_cancel, use_container_width=True)

# --- 6. BIẾN ĐỘNG THEO GIỜ ---
st.markdown("---")
st.subheader("⏰ Biến động theo khung giờ (Hourly Trend)")
hourly_data = df_filtered.groupby(['hour_time', 'status']).size().reset_index(name='count')
fig_line = px.line(hourly_data, x='hour_time', y='count', color='status', 
                   markers=True, color_discrete_map={'COMPLETED': '#636EFA', 'CANCELLED': '#EF553B'})
st.plotly_chart(fig_line, use_container_width=True)