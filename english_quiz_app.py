# =============================================
# 📚 영어 단어 종합 테스트 웹앱 (다중 모드)
# =============================================
import streamlit as st
from gtts import gTTS
import tempfile
import random

# ----------------------------
# 단어 데이터 (한글 정의 추가)
# ----------------------------
words = [
    # 기존 단어들
    ("grain", "곡물", "a small, dry fruit of a cereal grass such as wheat.", "밀과 같은 곡물의 작고 마른 열매"),
    ("flour", "밀가루", "powder used for baking.", "빵을 만들 때 사용하는 가루"),
    ("pop", "튀어 나오다", "to break open with a short, sharp, explosive sound.", "짧고 날카로운 폭발음과 함께 갑자기 터지다"),
    ("nectar", "꽃꿀, 꿀", "a sweet liquid in flowers.", "꽃 안에 있는 달콤한 액체"),
    ("hive", "벌집", "where a group of bees live.", "벌들이 무리지어 사는 곳"),
    ("sap", "수액", "the liquid that comes from a tree.", "나무에서 나오는 액체"),
    ("drip", "뚝뚝 떨어지다", "to fall in small amounts.", "조금씩 떨어지다"),
    ("trade", "교환하다", "changing one thing for another.", "한 가지를 다른 것으로 바꾸다"),
    ("chop", "자르다", "to cut something with an ax.", "도끼로 무언가를 자르다"),
    ("imagine", "상상하다", "to think of or create something not real in your mind.", "마음속에서 실제가 아닌 것을 생각하거나 만들어내다"),
    
    # 새로 추가된 단어들 (이미지에서 추출)
    ("great", "훌륭한", "of better quality", "더 좋은 품질의"),
    ("intend", "의도하다", "to have as plan or purposes", "계획이나 목적으로 가지다"),
    ("soon", "곧", "shortly; in the near future", "가까운 미래에; 곧"),
    ("laugh", "웃다", "what you do to show that something is funny", "뭔가 재미있다는 것을 보여주기 위해 하는 것"),
    ("do", "끝내다", "finished; completed", "끝마친; 완료된"),
    ("crop", "농작물", "plants that are grown for eating", "먹기 위해 기르는 식물"),
    ("hop", "폴짝폴짝 뛰다", "to move quickly by making small jumps", "작은 점프를 해서 빠르게 움직이다"),
    ("idea", "생각", "a suggestion or plan for doing something", "뭔가를 하기 위한 제안이나 계획"),
    ("unusual", "비정상적인", "not normal or usual", "보통이 아니거나 일반적이지 않은"),
    ("volume", "음량", "level of sound whether loud or soft", "큰지 작은지에 상관없는 소리의 정도"),
]

# ----------------------------
# 세션 상태 초기화
# ----------------------------
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = "definition_to_english"
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_data' not in st.session_state:
    # 기본값으로 전체 단어 사용
    st.session_state.quiz_data = random.sample(words, len(words))
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False

# 단어 선택 상태 초기화 (기본값: 전체 선택)
for i in range(len(words)):
    if f'word_{i}' not in st.session_state:
        st.session_state[f'word_{i}'] = True

# ----------------------------
# 웹앱 인터페이스 구성
# ----------------------------
st.set_page_config(
    page_title="영어 단어 종합 테스트", 
    page_icon="📚", 
    layout="wide",  # 모바일에서 더 넓은 화면 활용
    initial_sidebar_state="collapsed"  # 모바일에서 사이드바 기본 접힘
)

st.title("📚 영어 단어 종합 테스트")
st.write("**다양한 모드로 영어 단어를 학습하세요!**")

# 모바일 최적화 CSS
st.markdown("""
<style>
    /* 모바일 친화적 스타일 */
    .stButton > button {
        height: 3rem;
        font-size: 1rem;
        font-weight: bold;
    }
    
    .stSelectbox > div > div {
        font-size: 0.9rem;
    }
    
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        height: 3rem;
    }
    
    .stExpander > div {
        border-radius: 0.5rem;
    }
    
    /* 모바일에서 여백 최적화 */
    @media (max-width: 768px) {
        .stButton > button {
            height: 2.5rem;
            font-size: 0.9rem;
        }
        
        .stTextInput > div > div > input {
            font-size: 1rem;
            height: 2.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 모바일 친화적 컨테이너
with st.container():
    # 단어 선택 섹션 - 모바일에서 기본 접힘
    with st.expander("📝 테스트할 단어 선택 (기본: 전체 선택)", expanded=False):
        st.write("테스트에 포함할 단어를 선택하세요:")
        
        # 전체 선택/해제 버튼 - 모바일 최적화
        col_all, col_clear = st.columns(2)
        with col_all:
            if st.button("✅ 전체 선택", key="select_all", use_container_width=True):
                for i in range(len(words)):
                    st.session_state[f"word_{i}"] = True
                st.rerun()
        
        with col_clear:
            if st.button("❌ 전체 해제", key="clear_all", use_container_width=True):
                for i in range(len(words)):
                    st.session_state[f"word_{i}"] = False
                st.rerun()
        
        # 단어별 체크박스 - 모바일에서 2개 컬럼으로 변경
        cols = st.columns(2)  # 모바일 화면을 고려해 3개에서 2개로 변경
        for i, (eng, kor, eng_def, kor_def) in enumerate(words):
            with cols[i % 2]:
                # 기본값을 True로 설정 (전체 선택 상태)
                default_value = st.session_state.get(f"word_{i}", True)
                selected = st.checkbox(
                    f"{eng} ({kor})",
                    value=default_value,
                    key=f"word_{i}",
                    help=f"🇺🇸 English: {eng_def}\n🇰🇷 한글: {kor_def}"
                )

    # 선택된 단어 개수 표시
    selected_words = []
    for i, word in enumerate(words):
        if st.session_state.get(f"word_{i}", True):  # 기본값 True
            selected_words.append(word)

    if len(selected_words) == 0:
        st.warning("⚠️ 최소 1개 이상의 단어를 선택해주세요!")
        st.stop()

    st.success(f"✅ 선택된 단어: **{len(selected_words)}개** / 전체 {len(words)}개")

    # 설정 옵션들 - 모바일에서 세로 배치
    st.markdown("### ⚙️ 설정")
    
    # 모바일에서는 2행으로 나누어 배치
    col1, col2 = st.columns(2)
    
    with col1:
        # 테스트 모드 선택
        quiz_modes = {
            "definition_to_english": "📖 Definition → English",
            "english_to_korean": "🔤 English → Korean", 
            "korean_to_english": "🇰🇷 Korean → English"
        }
        
        selected_mode = st.selectbox(
            "🎯 테스트 모드:",
            options=list(quiz_modes.keys()),
            format_func=lambda x: quiz_modes[x],
            key="mode_selector"
        )
        
        # 음성 속도 선택
        audio_speed = st.selectbox(
            "🎵 음성 속도:",
            options=["slow", "normal"],
            format_func=lambda x: "🐢 느린 속도" if x == "slow" else "🐰 정상 속도",
            key="audio_speed"
        )
    
    with col2:
        # 자동재생 선택
        auto_play_enabled = st.selectbox(
            "🔄 자동재생:",
            options=[True, False],
            format_func=lambda x: "✅ 자동재생" if x else "❌ 수동재생",
            key="auto_play_enabled",
            index=0  # 기본값: 자동재생 켜짐
        )
        
        # Definition 언어 선택
        definition_language = st.selectbox(
            "📖 Definition 언어:",
            options=["english", "korean"],
            format_func=lambda x: "🇺🇸 English" if x == "english" else "🇰🇷 한글",
            key="definition_language",
            index=0  # 기본값: English
        )

# 헬퍼 함수: TTS 생성 및 재생
def play_audio(text, language="en", slow=False):
    try:
        tts = gTTS(text=text, lang=language, slow=slow)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")
    except Exception as e:
        st.error(f"오디오 생성 중 오류가 발생했습니다: {e}")

# 퀴즈 리셋 함수
def reset_quiz():
    st.session_state.current_question = 0
    st.session_state.score = 0
    
    # 선택된 단어만 퀴즈 데이터로 사용
    selected_words = []
    for i, word in enumerate(words):
        if st.session_state.get(f"word_{i}", True):  # 기본값 True
            selected_words.append(word)
    
    # 선택된 단어가 있으면 랜덤하게 섞어서 사용
    if selected_words:
        st.session_state.quiz_data = random.sample(selected_words, len(selected_words))
    else:
        st.session_state.quiz_data = []
    
    st.session_state.user_answer = ""
    st.session_state.show_result = False
    st.session_state.quiz_completed = False
    
    # 자동재생 상태 초기화
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("auto_played_")]
    for key in keys_to_remove:
        del st.session_state[key]

# 모드별 문제 정보 가져오기
def get_question_info(word_data, mode):
    eng_word, kor_meaning, eng_definition, kor_definition = word_data
    
    # Definition 언어 선택에 따른 정의 및 언어 설정
    if st.session_state.definition_language == "korean":
        definition_text = kor_definition
        definition_lang = "ko"
        definition_type = "📖 한글 Definition"
        other_definition = f"🇺🇸 English Definition: {eng_definition}"
    else:
        definition_text = eng_definition
        definition_lang = "en"
        definition_type = "📖 English Definition"
        other_definition = f"🇰🇷 한글 Definition: {kor_definition}"
    
    if mode == "definition_to_english":
        return {
            "question_text": definition_text,
            "question_lang": definition_lang,
            "answer": eng_word.lower(),
            "display_answer": eng_word,
            "hint": f"🇰🇷 한글 뜻: {kor_meaning}",
            "question_type": definition_type,
            "answer_type": "English 단어",
            "other_definition": other_definition
        }
    elif mode == "english_to_korean":
        return {
            "question_text": eng_word,
            "question_lang": "en",
            "answer": kor_meaning,
            "display_answer": kor_meaning,
            "hint": f"📘 Definition: {definition_text}",
            "question_type": "🔤 English 단어",
            "answer_type": "한글 뜻",
            "other_definition": other_definition
        }
    elif mode == "korean_to_english":
        return {
            "question_text": kor_meaning,
            "question_lang": "ko",
            "answer": eng_word.lower(),
            "display_answer": eng_word,
            "hint": f"📘 Definition: {definition_text}",
            "question_type": "🇰🇷 한글 뜻",
            "answer_type": "English 단어",
            "other_definition": other_definition
        }

# 퀴즈 모드 및 단어 선택 변경 감지는 위에서 처리됨

# 모드 변경 시 퀴즈 리셋
if selected_mode != st.session_state.quiz_mode:
    st.session_state.quiz_mode = selected_mode
    reset_quiz()

# 단어 선택 변경 감지를 위한 체크
current_selection = [st.session_state.get(f"word_{i}", True) for i in range(len(words))]
if 'previous_selection' not in st.session_state:
    st.session_state.previous_selection = current_selection

# 단어 선택이 변경되면 퀴즈 리셋
if current_selection != st.session_state.previous_selection:
    st.session_state.previous_selection = current_selection
    reset_quiz()
    st.rerun()

# 진행률 표시
if not st.session_state.quiz_completed:
    if len(st.session_state.quiz_data) > 0:
        progress = st.session_state.current_question / len(st.session_state.quiz_data)
        st.progress(progress)
        st.write(f"**진행률:** {st.session_state.current_question}/{len(st.session_state.quiz_data)} | **점수:** {st.session_state.score}점")
    else:
        st.error("선택된 단어가 없습니다. 단어를 선택해주세요.")

# 퀴즈 완료 화면
if st.session_state.quiz_completed:
    st.balloons()
    final_score = st.session_state.score
    total_questions = len(st.session_state.quiz_data)
    percentage = (final_score / total_questions) * 100
    
    st.markdown("## 🎉 테스트 완료!")
    st.markdown(f"### 최종 점수: **{final_score}/{total_questions}** ({percentage:.1f}%)")
    
    if percentage >= 90:
        st.success("🌟 완벽해요! 훌륭한 실력입니다!")
    elif percentage >= 70:
        st.success("👍 잘했어요! 좋은 점수네요!")
    elif percentage >= 50:
        st.warning("📚 괜찮아요! 조금 더 연습해보세요!")
    else:
        st.info("💪 다시 도전해보세요! 연습하면 늘어날 거예요!")
    
    if st.button("🔄 다시 시작", key="restart", use_container_width=True):
        reset_quiz()
        st.rerun()

# 현재 문제 진행
elif st.session_state.current_question < len(st.session_state.quiz_data):
    current_word = st.session_state.quiz_data[st.session_state.current_question]
    question_info = get_question_info(current_word, st.session_state.quiz_mode)
    
    # 모바일 친화적 컨테이너
    with st.container():
        st.markdown(f"## 문제 {st.session_state.current_question + 1}")
        st.markdown(f"**모드:** {quiz_modes[st.session_state.quiz_mode]}")
        
        # 자동 재생 기능 - 자동재생이 활성화된 경우에만
        auto_play_key = f"auto_played_{st.session_state.current_question}_{st.session_state.quiz_mode}_{st.session_state.definition_language}"
        if st.session_state.auto_play_enabled and auto_play_key not in st.session_state:
            st.session_state[auto_play_key] = True
            speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
            lang_text = "한글" if st.session_state.definition_language == "korean" else "English"
            st.info(f"🎵 {lang_text} {speed_text}로 자동 재생 중: '{question_info['question_text']}'")
            play_audio(question_info['question_text'], question_info['question_lang'], slow=(st.session_state.audio_speed == "slow"))
        
        # 수동재생 모드일 때 안내 메시지
        if not st.session_state.auto_play_enabled and auto_play_key not in st.session_state:
            st.session_state[auto_play_key] = True
            lang_text = "한글" if st.session_state.definition_language == "korean" else "English"
            st.info(f"🎧 아래 버튼을 클릭하여 {lang_text} 음성을 들어보세요!")
        
        # 문제 재생 버튼 제목 변경
        button_title = f"### 🎧 {question_info['question_type']}을(를) " + ("다시 들어보세요:" if st.session_state.auto_play_enabled else "들어보세요:")
        st.markdown(button_title)
        
        # 모바일에서 버튼들을 세로로 배치
        # 재생 버튼들
        if st.button(f"🔊 {question_info['question_type']} " + ("다시 듣기" if st.session_state.auto_play_enabled else "듣기"), 
                    key=f"play_{st.session_state.current_question}", 
                    use_container_width=True):
            speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
            st.write(f"🎵 {speed_text}로 재생 중: '{question_info['question_text']}'")
            play_audio(question_info['question_text'], question_info['question_lang'], slow=(st.session_state.audio_speed == "slow"))
        
        # 반대 속도로 재생하는 버튼
        opposite_speed = "slow" if st.session_state.audio_speed == "normal" else "normal"
        opposite_text = "느린 속도" if opposite_speed == "slow" else "정상 속도"
        if st.button(f"🎵 {opposite_text}로 듣기", 
                    key=f"alt_play_{st.session_state.current_question}", 
                    use_container_width=True):
            st.write(f"🎵 {opposite_text}로 재생 중: '{question_info['question_text']}'")
            play_audio(question_info['question_text'], question_info['question_lang'], slow=(opposite_speed == "slow"))
        
        # 힌트 섹션 - 모바일에서 기본 접힘
        with st.expander(f"📖 {question_info['question_type']} 텍스트 보기 (힌트)", expanded=False):
            st.write(f"💡 **{question_info['question_type']}:** {question_info['question_text']}")
            st.write(f"🔍 **힌트:** {question_info['hint']}")
            st.write(f"🌐 **{question_info['other_definition']}**")
            
            # Definition 음성 재생 버튼들 - 모바일에서 세로 배치
            if st.button(f"🔊 현재 Definition 듣기", 
                        key=f"hint_current_{st.session_state.current_question}", 
                        use_container_width=True):
                speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
                st.write(f"🎵 {speed_text}로 재생 중")
                play_audio(question_info['question_text'], question_info['question_lang'], slow=(st.session_state.audio_speed == "slow"))
            
            # 다른 언어 Definition 재생
            if st.session_state.definition_language == "korean":
                other_def_text = st.session_state.quiz_data[st.session_state.current_question][2]  # English definition
                other_def_lang = "en"
                other_def_label = "English Definition"
            else:
                other_def_text = st.session_state.quiz_data[st.session_state.current_question][3]  # Korean definition
                other_def_lang = "ko"
                other_def_label = "한글 Definition"
                
            if st.button(f"🔊 {other_def_label} 듣기", 
                        key=f"hint_other_{st.session_state.current_question}", 
                        use_container_width=True):
                speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
                st.write(f"🎵 {speed_text}로 재생 중")
                play_audio(other_def_text, other_def_lang, slow=(st.session_state.audio_speed == "slow"))
        
        # 사용자 입력
        st.markdown(f"### ✏️ {question_info['answer_type']}을(를) 입력하세요:")
        user_input = st.text_input(
            f"{question_info['answer_type']}을(를) 입력하세요:", 
            key=f"input_{st.session_state.current_question}",
            placeholder=f"{question_info['answer_type']}을(를) 입력하세요..."
        )
        
        # 답안 제출 버튼들 - 모바일에서 세로 배치
        if st.button("✅ 제출", key=f"submit_{st.session_state.current_question}", use_container_width=True):
            if user_input.strip():
                if st.session_state.quiz_mode == "english_to_korean":
                    st.session_state.user_answer = user_input.strip()
                else:
                    st.session_state.user_answer = user_input.strip().lower()
                st.session_state.show_result = True
                st.rerun()
            else:
                st.warning("답을 입력해주세요!")
        
        # 추가 버튼들을 2개 컬럼으로 배치 (모바일에서도 적당한 크기)
        col_hint, col_skip = st.columns(2)
        
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
        
        # 정답 발음 재생
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
        
        # 정답 발음 재생
        st.write("🔊 정답 발음:")
        speed_text = "느린 속도" if st.session_state.audio_speed == "slow" else "정상 속도"
        st.write(f"🎵 {speed_text}로 재생")
        if st.session_state.quiz_mode == "english_to_korean":
            play_audio(question_info['display_answer'], "ko", slow=(st.session_state.audio_speed == "slow"))
        else:
            play_audio(question_info['display_answer'], "en", slow=(st.session_state.audio_speed == "slow"))
    
    # 다음 문제로 이동 버튼 - 모바일에서 전체 너비 사용
    if st.button("➡️ 다음 문제로", key="next_question", use_container_width=True):
        st.session_state.current_question += 1
        st.session_state.show_result = False
        st.session_state.user_answer = ""
        
        if st.session_state.current_question >= len(st.session_state.quiz_data):
            st.session_state.quiz_completed = True
        
        st.rerun()

# 사이드바 - 진행 상황 및 옵션
with st.sidebar:
    st.markdown("## 📊 테스트 정보")
    st.write(f"**현재 모드:** {quiz_modes[st.session_state.quiz_mode]}")
    st.write(f"**선택된 단어:** {len(selected_words)}개")
    st.write(f"**전체 단어:** {len(words)}개")
    if len(st.session_state.quiz_data) > 0:
        st.write(f"**현재 문제:** {st.session_state.current_question + 1}/{len(st.session_state.quiz_data)}")
        st.write(f"**현재 점수:** {st.session_state.score}점")
        
        if st.session_state.current_question > 0:
            accuracy = (st.session_state.score / st.session_state.current_question) * 100
            st.write(f"**정답률:** {accuracy:.1f}%")
    
    st.markdown("---")
    st.markdown("## 🎯 테스트 모드")
    st.write("📖 **Definition → English**")
    st.write("   영어 정의를 듣고 단어 맞추기")
    st.write("🔤 **English → Korean**")
    st.write("   영어 단어를 듣고 한글 뜻 맞추기") 
    st.write("🇰🇷 **Korean → English**")
    st.write("   한글 뜻을 듣고 영어 단어 맞추기")
    
    st.markdown("---")
    st.markdown("## 📝 사용 방법")
    st.write("1. 📝 **테스트할 단어** 선택")
    st.write("2. 🎯 **테스트 모드** 선택")
    st.write("3. 🎵 **음성 속도** 선택")
    st.write("   • 🐢 느린 속도 (기본값) / 🐰 정상 속도")
    st.write("4. 🔄 **자동재생** 설정")
    st.write("   • ✅ 자동재생: 문제 시작 시 즉시 재생")
    st.write("   • ❌ 수동재생: 버튼 클릭 시 재생")
    st.write("5. 📖 **Definition 언어** 선택")
    st.write("   • 🇺🇸 English / 🇰🇷 한글")
    st.write("6. 🔊 **듣기** 버튼 클릭 (수동재생 시)")
    st.write("7. 음성을 듣고 답 입력")
    st.write("8. ✅ **제출** 버튼 클릭")
    st.write("💡 **Tip:** 힌트에서 두 언어 모두 들을 수 있어요!")
    
    st.markdown("---")
    if st.button("🔄 테스트 다시 시작", use_container_width=True):
        reset_quiz()
        st.rerun()
