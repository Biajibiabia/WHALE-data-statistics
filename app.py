import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# 设置页面配置
st.set_page_config(page_title="WHALE数据交叉统计工具 (华西本部)", layout="wide", initial_sidebar_state="expanded")

# 数据加载函数
@st.cache_data(show_spinner=False)
def load_data():
    try:
        # 从 Google Drive 加载 basic.csv 和 clinical_data.csv
        basic_url = "https://drive.google.com/uc?export=download&id=1CSU9AMA3o-1j_3UFLGc2efCMs8MhR3ek"
        clinical_url = "https://drive.google.com/uc?export=download&id=1rSNVF2QINz1FMusUunH_KxvSQJKJitXD"
        basic = pd.read_csv(basic_url, usecols=['id_patientarchive', 'id_patient', 'year'])
        clinical_data = pd.read_csv(clinical_url, usecols=['id_patientarchive'])
        
        # 本地文件路径
        data_dir = Path.cwd()
        xue_sample = pd.read_csv(data_dir / "xue_sample.csv", usecols=['id_patientarchive', 'year'])
        baimo_sample = pd.read_csv(data_dir / "baimo_sample.csv", usecols=['id_patientarchive', 'year'])
        wgs = pd.read_csv(data_dir / "wgs.csv", usecols=['id_patientarchive'])
        
        # 提取2019年及之后的血浆和白膜层数据
        xue_sample_2019 = xue_sample[xue_sample['year'] >= 2019]
        baimo_sample_2019 = baimo_sample[baimo_sample['year'] >= 2019]
        
        return basic, xue_sample, baimo_sample, wgs, clinical_data, xue_sample_2019, baimo_sample_2019
    except Exception as e:
        st.error(f"数据加载失败：{str(e)}")
        return None, None, None, None, None, None, None

# 计算体检次数
@st.cache_data
def get_exam_counts(basic):
    if basic is None:
        return None
    return basic.groupby('id_patientarchive')['id_patient'].nunique().reset_index(name='exam_count')

# 主界面
def main():
    st.title("WHALE数据交叉统计工具 (华西本部)")
    st.markdown("基于体检、血浆、白膜层、WGS和临床数据的交叉统计分析工具")

    # 加载数据
    basic, xue_sample, baimo_sample, wgs, clinical_data, xue_sample_2019, baimo_sample_2019 = load_data()
    if basic is None:
        return
    
    exam_counts = get_exam_counts(basic)
    if exam_counts is None:
        return

    # 侧边栏说明
    with st.sidebar:
        st.header("使用说明")
        st.markdown("""
        - **体检次数门槛**：选择体检次数范围。
        - **交叉数据集**：多选需要交叉的数据类型。
        - 点击“计算交叉人数”查看结果。
        - 数据来源：华西本部 WHALE 项目。
        """)

    # 第一部分：数据类别总览
    st.header("数据类别总览")
    stats = {
        '体检数据总人数': basic['id_patientarchive'].nunique(),
        '体检≥3次': len(exam_counts[exam_counts['exam_count'] >= 3]),
        '体检≥10次': len(exam_counts[exam_counts['exam_count'] >= 10]),
        '血浆样本': xue_sample['id_patientarchive'].nunique(),
        '血浆（19年后）': xue_sample_2019['id_patientarchive'].nunique(),
        '白膜层样本': baimo_sample['id_patientarchive'].nunique(),
        '白膜层（19年后）': baimo_sample_2019['id_patientarchive'].nunique(),
        'WGS表型': wgs['id_patientarchive'].nunique(),
        '临床数据': clinical_data['id_patientarchive'].nunique()
    }
    
    fig = px.bar(
        x=list(stats.keys()),
        y=list(stats.values()),
        labels={'x': '数据类别', 'y': '人数'},
        title='各数据类别人数统计',
        text=[f'{val:,}' for val in stats.values()],
    )
    fig.update_traces(
        textposition='outside',
        textfont_size=14,
        marker_color='#377B95',
        marker_line_color='#1F4E79',
        marker_line_width=1.5,
        opacity=0.9
    )
    fig.update_layout(
        title_font_size=22,
        title_x=0.5,
        xaxis_title_font_size=16,
        yaxis_title_font_size=16,
        font=dict(size=12, color="#333333"),
        plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.25,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.5)'),
        margin=dict(t=80, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 第二部分：交叉统计分析
    st.header("交叉统计分析")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        exam_threshold = st.selectbox(
            "选择体检次数门槛",
            options=["全部", "3次及以上", "10次及以上"],
            help="选择体检次数范围以筛选人群"
        )
    
    with col2:
        selected_datasets = st.multiselect(
            "选择交叉数据集 (可多选)",
            options=["血浆样本", "血浆（19年后）", "白膜层样本", "白膜层（19年后）", "WGS表型", "临床数据"],
            default=[],
            help="选择需要交叉分析的数据类型"
        )
    
    if st.button("计算交叉人数", key="calculate"):
        if not selected_datasets and exam_threshold == "全部":
            st.warning("请选择至少一个数据集或更具体的体检次数门槛")
        else:
            if exam_threshold == "全部":
                base_ids = set(basic['id_patientarchive'].unique())
            elif exam_threshold == "3次及以上":
                base_ids = set(exam_counts[exam_counts['exam_count'] >= 3]['id_patientarchive'])
            else:
                base_ids = set(exam_counts[exam_counts['exam_count'] >= 10]['id_patientarchive'])
            
            data_map = {
                "血浆样本": xue_sample,
                "血浆（19年后）": xue_sample_2019,
                "白膜层样本": baimo_sample,
                "白膜层（19年后）": baimo_sample_2019,
                "WGS表型": wgs,
                "临床数据": clinical_data
            }
            
            result_ids = base_ids
            for dataset_name in selected_datasets:
                dataset_ids = set(data_map[dataset_name]['id_patientarchive'].unique())
                result_ids = result_ids.intersection(dataset_ids)
            
            condition_str = f"{exam_threshold}体检 + {', '.join(selected_datasets) if selected_datasets else '无额外数据集'}"
            st.success(f"**筛选条件**：{condition_str}")
            st.info(f"**交叉人数结果**：{len(result_ids):,} 人")

if __name__ == "__main__":
    main()