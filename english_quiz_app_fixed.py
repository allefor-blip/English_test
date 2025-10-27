import streamlit as st
import csv
import random
import tempfile
import os
import time
import uuid
import atexit
from gtts import gTTS

# 페이지 설정
st.set_page_config(
    page_title="🎯 영어 단어 학습 퀴즈",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"  # 사이드바를 기본적으로 닫힌 상태로 설정
)

# 세션 상태 초기화
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = "definition_to_english"
if 'audio_speed' not in st.session_state:
    st.session_state.audio_speed = "normal"
if 'auto_play_enabled' not in st.session_state:
    st.session_state.auto_play_enabled = True
if 'word_order' not in st.session_state:
    st.session_state.word_order = "random"
if 'definition_language' not in st.session_state:
    st.session_state.definition_language = "english"

# 앱 시작 시 이전 임시 오디오 파일들 정리
def cleanup_old_audio_files():
    try:
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith("tts_audio_") and filename.endswith(".mp3"):
                try:
                    file_path = os.path.join(temp_dir, filename)
                    os.unlink(file_path)
                except:
                    pass  # 삭제 실패 시 무시
    except:
        pass  # 전체 정리 실패 시 무시

# 처음 로드 시에만 정리 실행
if 'cleanup_done' not in st.session_state:
    cleanup_old_audio_files()
    st.session_state.cleanup_done = True

# CSV 파일 읽기 함수 (BOM 문제 해결)
def load_words_from_csv():
    try:
        words = []
        
        # 먼저 업로드된 파일이 있는지 확인
        upload_path = '/mnt/user-data/uploads/vocabulary_list.csv'
        local_path = 'vocabulary_list.csv'
        
        file_path = None
        if os.path.exists(upload_path):
            file_path = upload_path
        elif os.path.exists(local_path):
            file_path = local_path
        else:
            st.error("❌ vocabulary_list.csv 파일을 찾을 수 없습니다.")
            return []
        
        # BOM을 제거하여 파일 읽기
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read()
            # BOM이 있으면 제거
            if content.startswith('\ufeff'):
                content = content[1:]
            
            # 문자열을 다시 파일처럼 처리
            import io
            csv_file = io.StringIO(content)
            csv_reader = csv.reader(csv_file)
            
            # 헤더 읽기 (표시하지 않음)
            header = next(csv_reader, None)
            if header:
                # 첫 번째 컬럼에서 남은 BOM 문자들 제거
                if header[0].startswith('\ufeff'):
                    header[0] = header[0][1:]
                if header[0].startswith('\\xef\\xbb\\xbf'):
                    header[0] = header[0][11:]
                
                # CSV 구조: Week, NO, English, Korean, POS, Definition, Definition_Korean, Example, Example_Korean
                for row_num, row in enumerate(csv_reader, start=2):
                    if len(row) >= 6:  # 최소 Definition까지 있어야 함
                        # 각 필드 정리
                        week = row[0].strip() if len(row) > 0 else ""
                        no = row[1].strip() if len(row) > 1 else ""
                        english = row[2].strip() if len(row) > 2 else ""
                        korean = row[3].strip() if len(row) > 3 else ""
                        pos = row[4].strip() if len(row) > 4 else ""
                        eng_definition = row[5].strip() if len(row) > 5 else ""
                        kor_definition = row[6].strip() if len(row) > 6 else ""
                        example = row[7].strip() if len(row) > 7 else ""
                        example_korean = row[8].strip() if len(row) > 8 else ""
                        
                        # 표준 8개 컬럼 구조로 저장
                        standard_row = [week, no, english, korean, eng_definition, kor_definition, example, example_korean]
                        
                        # 필수 데이터 체크
                        if english and korean:
                            words.append(tuple(standard_row))
                        else:
                            st.warning(f"⚠️ {row_num}번째 행에 필수 데이터가 없습니다: {row}")
                    else:
                        st.warning(f"⚠️ {row_num}번째 행의 데이터가 부족합니다: {row}")
        
        return words
    except FileNotFoundError:
        st.error("❌ vocabulary_list.csv 파일을 찾을 수 없습니다.")
        return []
    except Exception as e:
        st.error(f"❌ 파일 읽기 오류: {str(e)}")
        return []

# CSV 파일에서 단어 데이터 로드
words = load_words_from_csv()

# 퀴즈 리셋 함수
def reset_quiz(filtered_indices=None):
    st.session_state.current_question = 0
    st.session_state.score = 0
    
    # 필터링된 인덱스가 제공되면 사용, 아니면 전체 단어 사용
    if filtered_indices is not None:
        indices_to_check = filtered_indices
    else:
        indices_to_check = list(range(len(words)))
    
    # 선택된 단어만 퀴즈 데이터로 사용
    selected_words = []
    for i in indices_to_check:
        # 기본값을 True로 설정하여 처음에는 모든 단어가 선택되도록 함
        if st.session_state.get(f"word_{i}", True):
            selected_words.append(words[i])
    
    # 단어 순서 설정에 따라 정렬
    if selected_words:
        if st.session_state.get("word_order", "random") == "random":
            # 무작위로 섞기
            st.session_state.quiz_data = random.sample(selected_words, len(selected_words))
        else:
            # No열 순서대로 정렬
            def sort_key(word_data):
                if len(word_data) >= 8:
                    week, no, *_ = word_data
                    try:
                        week_num = int(week) if week and week != 'nan' else 0
                        no_num = int(no) if no and no != 'nan' else 0
                        return (week_num, no_num)
                    except:
                        return (0, 0)
                else:
                    return (0, 0)
            
            st.session_state.quiz_data = sorted(selected_words, key=sort_key)
    else:
        st.session_state.quiz_data = []
    
    st.session_state.user_answer = ""
    st.session_state.show_result = False
    st.session_state.quiz_completed = False
    
    # 자동재생 상태 초기화
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("auto_played_")]
    for key in keys_to_remove:
        del st.session_state[key]

# vocabulary_list.csv 파일을 읽지 못한 경우 앱 실행 중단
if not words:
    st.error("❌ vocabulary_list.csv 파일을 읽을 수 없습니다.")
    st.info("📝 파일이 Python 스크립트와 같은 폴더에 있는지 확인해주세요.")
    st.stop()

# 퀴즈 진행 상태 확인
quiz_completed = (st.session_state.quiz_completed or 
                 st.session_state.current_question >= len(st.session_state.quiz_data))

quiz_in_progress = (len(st.session_state.quiz_data) > 0 and 
                   not quiz_completed and 
                   st.session_state.current_question < len(st.session_state.quiz_data))

# 앱 제목
st.title("🎯 영어 단어 학습 퀴즈")

# 퀴즈 완료 상태를 가장 먼저 체크
quiz_completed = (st.session_state.quiz_completed or 
                 (len(st.session_state.quiz_data) > 0 and 
                  st.session_state.current_question >= len(st.session_state.quiz_data)))

# 퀴즈가 완료되었다면 결과 화면만 표시
if quiz_completed and len(st.session_state.quiz_data) > 0:
    st.markdown("---")
    st.markdown("## 🎉 퀴즈 완료!")
    
    total_questions = len(st.session_state.quiz_data)
    correct_answers = st.session_state.score
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # 결과 메트릭 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 총 문제 수", total_questions)
    with col2:
        st.metric("✅ 정답 수", correct_answers)
    with col3:
        st.metric("🎯 정답률", f"{accuracy:.1f}%")
    
    # 성취도에 따른 메시지
    st.markdown("---")
    if accuracy >= 90:
        st.success("🏆 **훌륭합니다!** 완벽한 학습이었어요!")
    elif accuracy >= 70:
        st.success("🎯 **잘했습니다!** 좋은 성과네요!")
    elif accuracy >= 50:
        st.info("📚 **괜찮습니다!** 조금 더 연습해보세요!")
    else:
        st.info("💪 **다시 한 번 도전해보세요!** 연습이 실력을 만듭니다!")
    
    st.markdown("---")
    
    # 완료 후 선택 버튼들
    col_retry, col_new = st.columns(2)
    
    with col_retry:
        if st.button("🔄 같은 단어로 다시", use_container_width=True, type="primary"):
            # 같은 설정으로 퀴즈 다시 시작
            current_filtered = getattr(st.session_state, 'current_filtered_indices', list(range(len(words))))
            reset_quiz(current_filtered)
            st.rerun()
    
    with col_new:
        if st.button("🏠 새 설정으로 시작", use_container_width=True, type="secondary"):
            # 설정 화면으로 돌아가기
            st.session_state.quiz_data = []
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.show_result = False
            st.session_state.quiz_completed = False
            st.rerun()
    
    # 퀴즈 완료 시에는 여기서 앱 종료 (다른 화면 요소들 표시하지 않음)
    st.stop()

# 퀴즈 진행 상태 확인
quiz_in_progress = (len(st.session_state.quiz_data) > 0 and 
                   not quiz_completed and 
                   st.session_state.current_question < len(st.session_state.quiz_data))

# 퀴즈가 진행 중이 아닐 때만 부제목 표시
if not quiz_in_progress:
    st.markdown("### 🎧 듣기로 배우는 영어 단어 테스트")

# 퀴즈가 진행 중이 아닐 때만 설정 및 선택 화면 표시
if not quiz_in_progress:

    # CSS 스타일링 (모바일 최적화)
    st.markdown("""
    <style>
        /* 기본 스타일 */
        .stSelectbox > div > div > div {
            font-size: 1rem;
        }
        .stButton > button {
            width: 100%;
            font-size: 1rem;
            height: 2.5rem;
        }
        
        /* 모바일 최적화 */
        @media (max-width: 768px) {
            .stSelectbox > div > div > div {
                font-size: 0.9rem;
            }
            .stButton > button {
                font-size: 0.8rem;
                height: 2.2rem;
                padding: 0.25rem 0.5rem;
            }
            
            /* 체크박스 크기 조정 */
            .stCheckbox > label {
                font-size: 0.85rem !important;
                line-height: 1.2 !important;
            }
            
            /* 컬럼 간격 줄이기 */
            .css-1r6slb0 {
                gap: 0.5rem;
            }
            
            /* Week 선택 영역 최적화 */
            .week-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 0.5rem;
                margin: 1rem 0;
            }
        }
        
        /* 매우 작은 화면 (320px 이하) */
        @media (max-width: 320px) {
            .stButton > button {
                font-size: 0.7rem;
                height: 2rem;
                padding: 0.2rem 0.3rem;
            }
            .stCheckbox > label {
                font-size: 0.8rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # 퀴즈 모드 정의
    quiz_modes = {
        "definition_to_english": "📖 Definition → English",
        "english_to_korean": "🔤 English → Korean",
        "korean_to_english": "🇰🇷 Korean → English"
    }

    # 설정 섹션 (모바일 최적화)
    st.markdown("## 🎯 퀴즈 설정")

    # 모바일에서는 세로로, 데스크톱에서는 가로로 배치
    # 1행: 퀴즈 모드, 음성 속도
    col1, col2 = st.columns(2)

    with col1:
        st.session_state.quiz_mode = st.selectbox(
            "🎯 테스트 모드",
            options=list(quiz_modes.keys()),
            format_func=lambda x: quiz_modes[x],
            index=list(quiz_modes.keys()).index(st.session_state.quiz_mode),
            key="quiz_mode_select"
        )

    with col2:
        st.session_state.audio_speed = st.selectbox(
            "🎵 음성 속도",
            ["normal", "slow"],
            format_func=lambda x: "정상 속도" if x == "normal" else "느린 속도",
            index=0 if st.session_state.audio_speed == "normal" else 1,
            key="audio_speed_select"
        )

    # 2행: 자동재생, 단어 순서
    col3, col4 = st.columns(2)

    with col3:
        st.session_state.auto_play_enabled = st.selectbox(
            "🔄 자동재생",
            [True, False],
            format_func=lambda x: "켜기" if x else "끄기",
            index=0 if st.session_state.auto_play_enabled else 1,
            key="auto_play_select"
        )

    with col4:
        st.session_state.word_order = st.selectbox(
            "📋 단어 순서",
            ["random", "sequential"],
            format_func=lambda x: "무작위" if x == "random" else "순서대로",
            index=0 if st.session_state.word_order == "random" else 1,
            key="word_order_select"
        )

    # 3행: Definition 언어 (필요한 경우에만)
    if st.session_state.quiz_mode == "definition_to_english":
        st.session_state.definition_language = st.selectbox(
            "📖 Definition 언어",
            ["english", "korean"],
            format_func=lambda x: "영어" if x == "english" else "한글",
            index=0 if st.session_state.definition_language == "english" else 1,
            key="definition_language_select"
        )
    else:
        # Definition 언어가 필요하지 않은 모드일 때는 간단히 표시
        st.info("📖 Definition 언어: 현재 모드에서는 사용되지 않습니다.")

    # 단어 선택 섹션
    st.markdown("## 📝 테스트할 단어 선택")

    # Week별 필터링
    weeks = sorted(list(set([word[0] for word in words if word[0] and word[0] != 'nan'])), key=lambda x: int(x) if x.isdigit() else 0)

    # Week 선택 영역
    st.markdown("### 📅 Week 선택")

    if weeks:
        # Week별 단어 수 계산
        week_word_counts = {}
        for week in weeks:
            week_word_counts[week] = len([word for word in words if word[0] == week])
        
        # 모바일 친화적인 체크박스 그리드
        if "selected_weeks_grid" not in st.session_state:
            st.session_state["selected_weeks_grid"] = set()
        
        selected_weeks = []
        
        # 모바일에서는 3개씩, 데스크톱에서는 5개씩
        # 화면 크기에 따라 자동 조정되도록 설정
        st.markdown('<div class="week-selection-container">', unsafe_allow_html=True)
        
        # 작은 화면에서는 3개씩, 큰 화면에서는 4개씩 배치
        cols_per_row = 3  # 모바일 최적화를 위해 3개로 설정
        weeks_chunks = [weeks[i:i + cols_per_row] for i in range(0, len(weeks), cols_per_row)]
        
        for chunk_idx, chunk in enumerate(weeks_chunks):
            cols = st.columns(len(chunk))
            
            for i, week in enumerate(chunk):
                with cols[i]:
                    # 체크박스 텍스트를 더 간결하게
                    checkbox_text = f"Week {week}"
                    help_text = f"{week_word_counts[week]}개 단어"
                    
                    # 고유한 키를 사용하여 버튼 클릭 시 체크박스가 올바르게 업데이트되도록 함
                    checkbox_key = f"week_checkbox_{week}_{st.session_state.get('week_selection_trigger', 0)}"
                    
                    is_selected = st.checkbox(
                        checkbox_text,
                        value=week in st.session_state["selected_weeks_grid"],
                        key=checkbox_key,
                        help=help_text
                    )
                    
                    # 선택 상태 업데이트
                    if is_selected:
                        st.session_state["selected_weeks_grid"].add(week)
                        selected_weeks.append(week)
                    else:
                        st.session_state["selected_weeks_grid"].discard(week)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 선택된 Week들을 숫자 순으로 정렬
        selected_weeks = sorted([w for w in selected_weeks if w in st.session_state["selected_weeks_grid"]], 
                               key=lambda x: int(x) if x.isdigit() else 0)
        
        # Week 선택 제어 버튼들 (모바일에서는 2x2 배치)
        st.markdown("#### 🎛️ Week 선택 제어")
        
        # 모바일에서는 2개씩 2줄로 배치
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 전체 선택", use_container_width=True, key="select_all_weeks"):
                st.session_state["selected_weeks_grid"] = set(weeks)
                # 강제로 페이지 새로고침을 위해 임시 상태 변경
                st.session_state["week_selection_trigger"] = st.session_state.get("week_selection_trigger", 0) + 1
                st.rerun()
                
            if st.button("🔄 선택 반전", use_container_width=True, key="invert_weeks"):
                current_selection = st.session_state["selected_weeks_grid"]
                new_selection = set(weeks) - current_selection
                st.session_state["selected_weeks_grid"] = new_selection
                # 강제로 페이지 새로고침을 위해 임시 상태 변경
                st.session_state["week_selection_trigger"] = st.session_state.get("week_selection_trigger", 0) + 1
                st.rerun()
        
        with col2:
            if st.button("❌ 전체 해제", use_container_width=True, key="deselect_all_weeks"):
                st.session_state["selected_weeks_grid"] = set()
                # 강제로 페이지 새로고침을 위해 임시 상태 변경
                st.session_state["week_selection_trigger"] = st.session_state.get("week_selection_trigger", 0) + 1
                st.rerun()
                
            # 최근 Week들만 선택 (예: 최근 5개)
            if st.button("⚡ 최근 5주", use_container_width=True, key="select_recent_weeks"):
                recent_weeks = sorted(weeks, key=lambda x: int(x) if x.isdigit() else 0)[-5:]
                st.session_state["selected_weeks_grid"] = set(recent_weeks)
                # 강제로 페이지 새로고침을 위해 임시 상태 변경
                st.session_state["week_selection_trigger"] = st.session_state.get("week_selection_trigger", 0) + 1
                st.rerun()
        
        # 선택된 Week 정보 표시 (더 간결하게)
        if selected_weeks:
            week_list = ', '.join(map(str, selected_weeks))
            total_week_words = sum(week_word_counts[week] for week in selected_weeks)
            
            # 긴 목록은 접기 기능으로 처리
            if len(selected_weeks) <= 5:
                st.success(f"📋 **선택:** Week {week_list}")
            else:
                with st.expander(f"📋 **선택된 Week ({len(selected_weeks)}개)** - 펼쳐서 보기"):
                    st.write(f"Week {week_list}")
            
            st.info(f"📊 **총 단어:** {total_week_words}개")
        else:
            st.warning("⚠️ Week가 선택되지 않았습니다. Week를 선택해주세요.")
            # Week가 선택되지 않으면 빈 리스트 반환
            selected_weeks = []
            
    else:
        selected_weeks = []
        st.error("Week 정보가 없습니다.")

    # 단어별 선택 제어 버튼 (모바일에서는 세로 배치)
    st.markdown("### 🎯 단어별 선택")

    # 모바일에서는 3개 버튼을 1열로 배치
    col1, col2, col3 = st.columns(1) if st.session_state.get('mobile_view', False) else st.columns(3)

    # 버튼 텍스트를 더 간결하게
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ 표시 단어 전체 선택", use_container_width=True, key="select_all_displayed"):
            # 필터링된 범위의 모든 단어 선택
            if st.session_state.get("selected_weeks_grid"):
                selected_weeks = list(st.session_state["selected_weeks_grid"])
                filtered_indices = [i for i, word in enumerate(words) if word[0] in selected_weeks]
                
                for i in filtered_indices:
                    st.session_state[f"word_{i}"] = True
                
                # 체크박스 새로고침을 위한 트리거
                st.session_state["word_selection_trigger"] = st.session_state.get("word_selection_trigger", 0) + 1
                st.rerun()
            else:
                st.warning("⚠️ 먼저 Week를 선택해주세요.")

    with col2:
        if st.button("❌ 표시 단어 전체 해제", use_container_width=True, key="deselect_all_displayed"):
            # 필터링된 범위의 모든 단어 해제
            if st.session_state.get("selected_weeks_grid"):
                selected_weeks = list(st.session_state["selected_weeks_grid"])
                filtered_indices = [i for i, word in enumerate(words) if word[0] in selected_weeks]
                
                for i in filtered_indices:
                    st.session_state[f"word_{i}"] = False
                
                # 체크박스 새로고침을 위한 트리거
                st.session_state["word_selection_trigger"] = st.session_state.get("word_selection_trigger", 0) + 1
                st.rerun()
            else:
                st.warning("⚠️ 먼저 Week를 선택해주세요.")

    with col3:
        if st.button("🔄 표시 단어 선택 반전", use_container_width=True, key="invert_displayed"):
            # 필터링된 범위의 단어 선택 상태 반전
            if st.session_state.get("selected_weeks_grid"):
                selected_weeks = list(st.session_state["selected_weeks_grid"])
                filtered_indices = [i for i, word in enumerate(words) if word[0] in selected_weeks]
                
                for i in filtered_indices:
                    current_state = st.session_state.get(f"word_{i}", True)
                    st.session_state[f"word_{i}"] = not current_state
                
                # 체크박스 새로고침을 위한 트리거
                st.session_state["word_selection_trigger"] = st.session_state.get("word_selection_trigger", 0) + 1
                st.rerun()
            else:
                st.warning("⚠️ 먼저 Week를 선택해주세요.")

# 필터링된 단어 인덱스 계산 (퀴즈 진행 중이 아닐 때만)
if not quiz_in_progress:
    if st.session_state.get("selected_weeks_grid"):
        selected_weeks = list(st.session_state["selected_weeks_grid"])
        filtered_indices = [i for i, word in enumerate(words) if word[0] in selected_weeks]
    else:
        # Week가 선택되지 않으면 빈 리스트 (아무 단어도 표시하지 않음)
        filtered_indices = []
else:
    # 퀴즈 진행 중일 때는 기존 필터링된 인덱스 유지
    filtered_indices = getattr(st.session_state, 'current_filtered_indices', [])

# 실제 선택된 단어 계산
actual_selected_words = []
for i in filtered_indices:
    if st.session_state.get(f"word_{i}", True):
        actual_selected_words.append(words[i])

# 퀴즈 설정 화면에서만 단어 선택 표시와 시작 버튼 표시
if not quiz_in_progress:
    # 선택된 단어 표시 (모바일 친화적인 Week별 그룹화)
    if filtered_indices:
        # 간결한 정보 표시
        st.markdown(f"**📊 선택 가능:** {len(filtered_indices)}개 | **선택됨:** {len(actual_selected_words)}개")
        
        # Week별로 그룹화하여 표시 (선택된 Week가 있을 때만)
        if st.session_state.get("selected_weeks_grid"):
            selected_weeks = list(st.session_state["selected_weeks_grid"])
            # 선택된 Week들을 순서대로 표시
            for week in sorted(selected_weeks, key=lambda x: int(x) if x.isdigit() else 0):
                week_words = [(i, word) for i, word in enumerate(words) if word[0] == week]
                
                if week_words:
                    # 접기 가능한 Week 섹션
                    with st.expander(f"📅 Week {week} ({len(week_words)}개 단어)", expanded=len(selected_weeks) <= 3):
                        
                        # Week별 선택/해제 버튼 (모바일에서는 2개씩)
                        col_week_all, col_week_none = st.columns(2)
                        
                        with col_week_all:
                            if st.button(f"✅ Week {week} 전체", key=f"select_all_week_{week}", use_container_width=True):
                                for i, word in week_words:
                                    st.session_state[f"word_{i}"] = True
                                # 체크박스 새로고침을 위한 트리거
                                st.session_state["word_selection_trigger"] = st.session_state.get("word_selection_trigger", 0) + 1
                                st.rerun()
                        
                        with col_week_none:
                            if st.button(f"❌ Week {week} 해제", key=f"deselect_all_week_{week}", use_container_width=True):
                                for i, word in week_words:
                                    st.session_state[f"word_{i}"] = False
                                # 체크박스 새로고침을 위한 트리거
                                st.session_state["word_selection_trigger"] = st.session_state.get("word_selection_trigger", 0) + 1
                                st.rerun()
                        
                        # 해당 Week의 단어들을 2개씩 한 줄에 표시 (모바일 최적화)
                        words_per_row = 2  # 모바일에서는 2개씩
                        num_rows = (len(week_words) + words_per_row - 1) // words_per_row
                        
                        for row in range(num_rows):
                            start_idx = row * words_per_row
                            end_idx = min(start_idx + words_per_row, len(week_words))
                            
                            cols = st.columns(words_per_row)
                            
                            for col_idx, (i, word) in enumerate(week_words[start_idx:end_idx]):
                                week_num, no, english, korean = word[0], word[1], word[2], word[3]
                                
                                with cols[col_idx]:
                                    checkbox_key = f"word_{i}"
                                    default_value = st.session_state.get(checkbox_key, True)
                                    
                                    # 더 간결한 라벨
                                    if no and no != 'nan':
                                        label = f"{week_num}-{no}: {english}"
                                    else:
                                        label = f"{english}"
                                    
                                    # 트리거를 포함한 고유 키 생성
                                    unique_checkbox_key = f"checkbox_{i}_{st.session_state.get('word_selection_trigger', 0)}"
                                    
                                    st.session_state[checkbox_key] = st.checkbox(
                                        label,
                                        value=default_value,
                                        key=unique_checkbox_key,
                                        help=f"🇰🇷 {korean}"
                                    )
    else:
        # Week가 선택되지 않았을 때 안내 메시지
        st.info("📋 **안내:** 위에서 Week를 먼저 선택해주세요.")
        st.write("💡 **사용법:**")
        st.write("1. 위의 Week 체크박스에서 원하는 Week를 선택")
        st.write("2. 선택된 Week의 단어들이 아래에 표시됩니다")
        st.write("3. 개별 단어를 선택하거나 해제할 수 있습니다")

    # 퀴즈 시작 버튼
    st.markdown("---")
    if len(actual_selected_words) > 0:
        if st.button("🎯 퀴즈 시작!", use_container_width=True, type="primary"):
            # 현재 필터링된 인덱스를 저장
            st.session_state.current_filtered_indices = filtered_indices
            reset_quiz(filtered_indices)
            st.rerun()
    else:
        st.warning("선택된 단어가 없습니다. 단어를 선택해주세요.")

# 퀴즈 모드 정의 (전역적으로 사용)
quiz_modes = {
    "definition_to_english": "📖 Definition → English",
    "english_to_korean": "🔤 English → Korean",
    "korean_to_english": "🇰🇷 Korean → English"
}

# gTTS를 사용한 음성 재생 함수 (Windows 호환성 개선)
def play_audio(text, lang="en", slow=False):
    try:
        # 고유한 파일명 생성으로 충돌 방지
        unique_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(temp_dir, f"tts_audio_{unique_id}.mp3")
        
        try:
            # TTS 생성
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(tmp_file_path)
            
            # 파일이 완전히 생성될 때까지 잠시 대기
            time.sleep(0.1)
            
            # 오디오 재생
            if os.path.exists(tmp_file_path):
                with open(tmp_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                # Base64로 인코딩
                import base64
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                # HTML5 audio 태그로 자동 재생
                audio_html = f"""
                <audio controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                """
                
                st.markdown(audio_html, unsafe_allow_html=True)
            
            # 재생 후 잠시 대기
            time.sleep(0.2)
            
        finally:
            # 안전한 파일 삭제 (여러 번 시도)
            for attempt in range(3):
                try:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        break
                except (OSError, PermissionError) as e:
                    if attempt < 2:
                        time.sleep(0.1)  # 잠시 대기 후 재시도
                    else:
                        # 마지막 시도도 실패 시 프로그램 종료 시 정리하도록 예약
                        def cleanup_file():
                            try:
                                if os.path.exists(tmp_file_path):
                                    os.unlink(tmp_file_path)
                            except:
                                pass
                        atexit.register(cleanup_file)
                        
    except Exception as e:
        st.error(f"음성 재생 오류: {str(e)}")
        st.info("💡 **대안 방법들:**")
        st.info("1. 브라우저의 음성 읽기 기능 사용")
        st.info("2. 앱을 다시 시작해보세요")
        st.info("3. 임시 파일 폴더를 정리해보세요")

# 퀴즈 모드에 따른 질문 정보 생성
def get_question_info(word_data, quiz_mode):
    if len(word_data) >= 8:
        week, no, eng, kor, eng_def, kor_def, example, example_korean = word_data
    else:
        # 데이터가 부족한 경우 기본값 설정
        eng, kor, eng_def, kor_def = word_data[:4] if len(word_data) >= 4 else ("Unknown", "알 수 없음", "No definition", "정의 없음")
        example, example_korean, week, no = "", "", "", ""
    
    if quiz_mode == "definition_to_english":
        # Definition 언어에 따라 선택
        if st.session_state.definition_language == "korean" and kor_def:
            question = kor_def
            audio_lang = "ko"
        else:
            question = eng_def if eng_def else "No definition available"
            audio_lang = "en"
        
        answer = eng.lower().strip()
        display_answer = eng
        answer_type = "영어 단어"
        hint = f"한글 뜻: {kor}"
        
    elif quiz_mode == "english_to_korean":
        question = eng
        answer = kor.lower().strip()
        display_answer = kor
        answer_type = "한글 뜻"
        hint = f"영어 정의: {eng_def}"
        audio_lang = "en"
        
    else:  # korean_to_english
        question = kor
        answer = eng.lower().strip()
        display_answer = eng
        answer_type = "영어 단어"
        hint = f"영어 정의: {eng_def}"
        audio_lang = "ko"
    
    return {
        "question": question,
        "answer": answer,
        "display_answer": display_answer,
        "answer_type": answer_type,
        "hint": hint,
        "audio_lang": audio_lang
    }

# 퀴즈 진행
if len(st.session_state.quiz_data) > 0 and st.session_state.current_question < len(st.session_state.quiz_data):
    current_word = st.session_state.quiz_data[st.session_state.current_question]
    question_info = get_question_info(current_word, st.session_state.quiz_mode)
    
    st.markdown("---")
    st.markdown(f"## 📝 문제 {st.session_state.current_question + 1}/{len(st.session_state.quiz_data)}")
    
    # 진행률 표시
    progress = (st.session_state.current_question + 1) / len(st.session_state.quiz_data)
    st.progress(progress)
    
    # 자동재생 및 문제 시작 시 자동 플레이
    auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
    
    # 문제 시작 시 항상 자동으로 한 번 재생 (자동재생 설정과 관계없이)
    if auto_play_key not in st.session_state:
        st.session_state[auto_play_key] = True
        speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
        st.write(f"🎵 {speed_text}로 자동 재생")
        play_audio(question_info["question"], question_info["audio_lang"], slow=(st.session_state.audio_speed == "slow"))
    
    # 문제 표시
    st.markdown(f"### 🔊 듣고 답하세요:")
    st.markdown(f"**{question_info['question']}**")
    
    # 추가 정보 표시 (접기/펼치기)
    with st.expander("📋 추가 정보 보기"):
        # 현재 단어의 모든 정보 표시
        if len(current_word) >= 8:
            week, no, eng, kor, eng_def, kor_def, example, example_korean = current_word
        elif len(current_word) >= 6:
            week, no, eng, kor, eng_def, kor_def = current_word
            example, example_korean = "", ""
        elif len(current_word) >= 4:
            eng, kor, eng_def, kor_def = current_word[:4]
            example, example_korean, week, no = "", "", "", ""
        else:
            eng, kor, eng_def, kor_def = "Unknown", "알 수 없음", "No definition", "정의 없음"
            example, example_korean, week, no = "", "", "", ""
        
        if week and week != 'nan' and week.strip():
            if no and no != 'nan' and no.strip():
                st.write(f"📅 **Week {week}-{no}**")
            else:
                st.write(f"📅 **Week {week}**")
        
        st.write(f"🔤 **English:** {eng}")
        st.write(f"🇰🇷 **한글:** {kor}")
        st.write(f"🇺🇸 **English Definition:** {eng_def}")
        st.write(f"🇰🇷 **한글 Definition:** {kor_def}")
        
        if example and example != 'nan' and example.strip():
            st.write(f"📝 **Example:** {example}")
            if st.button("🔊 예문 듣기", key=f"example_{st.session_state.current_question}"):
                play_audio(example, "en", slow=(st.session_state.audio_speed == "slow"))
        
        if example_korean and example_korean != 'nan' and example_korean.strip():
            st.write(f"📝 **예문:** {example_korean}")
            if st.button("🔊 한글 예문 듣기", key=f"example_ko_{st.session_state.current_question}"):
                play_audio(example_korean, "ko", slow=(st.session_state.audio_speed == "slow"))
    
    # 답안 입력
    st.markdown(f"### ✏️ **{question_info['answer_type']}**을(를) 입력하세요:")
    
    if not st.session_state.show_result:
        user_input = st.text_input(
            "답:",
            value="",
            placeholder=f"{question_info['answer_type']}을(를) 입력하세요...",
            key=f"input_{st.session_state.current_question}"
        )
        
        if st.button("✅ 제출", key=f"submit_{st.session_state.current_question}", use_container_width=True):
            if user_input.strip():
                st.session_state.user_answer = user_input.strip().lower()
                st.session_state.show_result = True
                st.rerun()
            else:
                st.warning("답을 입력해주세요!")
        
        # 추가 버튼들
        col_prev, col_hint, col_skip = st.columns(3)
        
        with col_prev:
            if st.session_state.current_question > 0:
                if st.button("⏮️ 이전 문제", key=f"prev_{st.session_state.current_question}", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.session_state.show_result = False
                    st.session_state.user_answer = ""
                    
                    prev_auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
                    if prev_auto_play_key in st.session_state:
                        del st.session_state[prev_auto_play_key]
                    
                    st.rerun()
        
        with col_hint:
            if st.button("🔊 정답 발음", key=f"hint_{st.session_state.current_question}", use_container_width=True):
                speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
                if st.session_state.quiz_mode == "english_to_korean":
                    st.write(f"🎵 {speed_text}로 정답 발음: '{question_info['display_answer']}'")
                    play_audio(question_info['display_answer'], "ko", slow=(st.session_state.audio_speed == "slow"))
                else:
                    st.write(f"🎵 {speed_text}로 정답 발음: '{question_info['display_answer']}'")
                    play_audio(question_info['display_answer'], "en", slow=(st.session_state.audio_speed == "slow"))
        
        with col_skip:
            if st.button("⏭️ 다음 문제", key=f"skip_{st.session_state.current_question}", use_container_width=True):
                st.session_state.current_question += 1
                st.session_state.show_result = False
                st.session_state.user_answer = ""
                
                next_auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
                if next_auto_play_key in st.session_state:
                    del st.session_state[next_auto_play_key]
                
                if st.session_state.current_question >= len(st.session_state.quiz_data):
                    st.session_state.quiz_completed = True
                st.rerun()

# 결과 표시
if st.session_state.show_result and not st.session_state.quiz_completed:
    current_word = st.session_state.quiz_data[st.session_state.current_question]
    question_info = get_question_info(current_word, st.session_state.quiz_mode)
    user_answer = st.session_state.user_answer
    
    st.markdown("---")
    
    if user_answer == question_info['answer']:
        st.success("🎉 정답입니다!")
        st.session_state.score += 1
        
        st.write("🔊 정답 발음:")
        speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
        st.write(f"🎵 {speed_text}로 재생")
        if st.session_state.quiz_mode == "english_to_korean":
            play_audio(question_info['display_answer'], "ko", slow=(st.session_state.audio_speed == "slow"))
        else:
            play_audio(question_info['display_answer'], "en", slow=(st.session_state.audio_speed == "slow"))
        
    else:
        st.error(f"❌ 틀렸습니다! 정답은 **'{question_info['display_answer']}'** 입니다.")
        st.write(f"🔍 힌트: {question_info['hint']}")
        
        st.write("🔊 정답 발음:")
        speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
        st.write(f"🎵 {speed_text}로 재생")
        if st.session_state.quiz_mode == "english_to_korean":
            play_audio(question_info['display_answer'], "ko", slow=(st.session_state.audio_speed == "slow"))
        else:
            play_audio(question_info['display_answer'], "en", slow=(st.session_state.audio_speed == "slow"))
    
    # 이전/다음 문제로 이동 버튼들
    col_prev_result, col_next_result = st.columns(2)
    
    with col_prev_result:
        if st.session_state.current_question > 0:
            if st.button("⬅️ 이전 문제로", key="prev_question_result", use_container_width=True):
                st.session_state.current_question -= 1
                st.session_state.show_result = False
                st.session_state.user_answer = ""
                
                prev_auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
                if prev_auto_play_key in st.session_state:
                    del st.session_state[prev_auto_play_key]
                
                st.rerun()
    
    with col_next_result:
        if st.button("➡️ 다음 문제로", key="next_question", use_container_width=True):
            st.session_state.current_question += 1
            st.session_state.show_result = False
            st.session_state.user_answer = ""
            
            next_auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
            if next_auto_play_key in st.session_state:
                del st.session_state[next_auto_play_key]
            
            if st.session_state.current_question >= len(st.session_state.quiz_data):
                st.session_state.quiz_completed = True
            
            st.rerun()

# 사이드바 (퀴즈 완료 시에는 표시하지 않음)
if not (st.session_state.quiz_completed or 
        (len(st.session_state.quiz_data) > 0 and 
         st.session_state.current_question >= len(st.session_state.quiz_data))):
    
    with st.sidebar:
        st.markdown("## 📊 테스트 정보")
        st.write(f"**현재 모드:** {quiz_modes[st.session_state.quiz_mode]}")
        
        # 선택된 Week 정보 표시
        if st.session_state.get("selected_weeks_grid", set()):
            selected_weeks_list = sorted(list(st.session_state["selected_weeks_grid"]), key=lambda x: int(x) if x.isdigit() else 0)
            selected_weeks_str = ", ".join(map(str, selected_weeks_list))
            st.write(f"**선택된 Week:** {selected_weeks_str}")
        else:
            st.write(f"**선택된 Week:** 전체")
        
        st.write(f"**선택된 단어:** {len(actual_selected_words)}개")
        st.write(f"**전체 단어:** {len(words)}개")
        
        if len(st.session_state.quiz_data) > 0:
            st.write(f"**현재 문제:** {st.session_state.current_question + 1}/{len(st.session_state.quiz_data)}")
            st.write(f"**현재 점수:** {st.session_state.score}점")
            
            if st.session_state.current_question > 0:
                accuracy = (st.session_state.score / st.session_state.current_question) * 100
                st.write(f"**정답률:** {accuracy:.1f}%")
        
        st.markdown("---")
        
        # 퀴즈 진행 중일 때와 아닐 때 다른 버튼 표시
        if quiz_in_progress:
            st.markdown("## 🎮 퀴즈 진행 중")
            st.info("퀴즈를 완료하거나 아래 버튼을 눌러 설정 화면으로 돌아갈 수 있습니다.")
            
            if st.button("🏠 설정 화면으로 돌아가기", use_container_width=True, type="secondary"):
                # 퀴즈 상태 초기화
                st.session_state.quiz_data = []
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.quiz_completed = False
                st.rerun()
        else:
            st.markdown("## 🎯 테스트 모드")
            st.write("📖 **Definition → English**")
            st.write("   영어 정의를 듣고 단어 맞추기")
            st.write("🔤 **English → Korean**")
            st.write("   영어 단어를 듣고 한글 뜻 맞추기") 
            st.write("🇰🇷 **Korean → English**")
            st.write("   한글 뜻을 듣고 영어 단어 맞추기")
            
            st.markdown("---")
            st.markdown("## 📝 사용 방법")
            st.write("1. 📅 **Week 체크박스**로 원하는 Week 선택")
            st.write("2. 📝 **테스트할 단어** 개별 선택")
            st.write("3. 🎯 **테스트 모드** 선택")
            st.write("4. 🎵 **음성 속도** 선택")
            st.write("5. 🔄 **자동재생** 설정")
            st.write("6. 📋 **단어 순서** 선택")
            st.write("7. 📖 **Definition 언어** 선택")
            st.write("8. 🎯 **퀴즈 시작!** 버튼 클릭")
            st.write("💡 **Tip:** 추가 정보에서 예문도 들을 수 있어요!")
        
        # 퀴즈 진행 중이 아닐 때만 다시 시작 버튼 표시
        if not quiz_in_progress:
            st.markdown("---")
            if st.button("🔄 설정 초기화", use_container_width=True):
                # 현재 필터링된 인덱스가 있다면 사용
                current_filtered = getattr(st.session_state, 'current_filtered_indices', list(range(len(words))))
                reset_quiz(current_filtered)
                st.rerun()
