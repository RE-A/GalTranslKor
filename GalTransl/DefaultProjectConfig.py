DEFAULT_PROJECT_CONFIG_YAML = """# 번역 백엔드 설정
backendSpecific:
  OpenAI-Compatible: # (ForGal/ForNovel/GenDic) OpenAI API 호환 인터페이스 공통
    tokens:
      - token: sk-example-key1
        endpoint: https://api.deepseek.com # 요청 주소. v1은 붙여도 되고 안 붙여도 됨
        modelName: deepseek-chat
        contextWindow: 128000 # 모델 컨텍스트 창(token). 에이전트가 문맥 압축 시점과 사용량 표시에 사용. 비우면 128000
      - token: sk-example-key2
        endpoint: https://openrouter.ai/api/v1/chat/completions # /chat/completions로 끝나면 v1을 자동으로 붙이지 않음
        modelName: deepseek/deepseek-chat-v3-0324:free
        stream: true # 토큰마다 스트리밍 요청 설정 가능
    tokenStrategy: "random" # 토큰 전략. random은 무작위 순환, fallback은 첫 항목 우선이며 [API 오류]나 [해석 오류]가 나면 다음 항목 사용
    # 생각(thinking) 매개변수는 서로 독립적이며, 비우거나 지우면 보내지 않음. 토큰 항목마다 따로 덮어쓸 수 있음.
    # enableThinking: true # extra_body.enable_thinking. Qwen3, DashScope, SiliconFlow 등에서 사용
    # thinkingType: enabled # extra_body.thinking.type. DeepSeek 등 thinking.type을 지원하는 API에서 사용
    # reasoningEffort: medium # reasoning_effort. OpenAI o 시리즈, GPT-5, 일부 중계에서 사용. 단계는 모델 지원에 맞춰 선택
    checkAvailable: true # 번역 전에 API 사용 가능 여부 확인[True/False]
    checkAvailableConcurrency: 4 # checkAvailable 단계의 동시 확인 수. 시작할 때 요청이 한꺼번에 몰리지 않게 함.[1-16]
    globalRequestRPM: 0 # 모든 작업이 함께 쓰는 요청 속도 제한(분당 요청 수). 0은 제한 없음.[0-60000]
    stream: true # 스트리밍 요청. API가 스트리밍을 지원하지 않을 때만 바꿈[True/False]
    apiTimeout: 300 # 요청 제한 시간(초)
    apiErrorWait: auto # API 오류(속도 제한 포함) 때 대기 시간. auto는 자동 조절[auto/0-120]
    maxApiRetries: 6 # 배치 하나의 최대 API 호출 수. 넘으면 실패로 표시하고 다음 배치로 진행.[1-100]
    genDicMaxApiRetries: 6 # GenDic 조각 하나의 최대 API 호출 수.[1-100]

  SakuraLLM: # (Sakura/Galtransl, 중국어 출력 모델)
    endpoints:
      - http://127.0.0.1:8080
    rewriteModelName: "" # 사용자 지정 모델 이름. ollama를 쓸 때는 바꿔야 함

# 플러그인. 목록은 프로그램에서 show-plugs로 보거나 plugins 폴더에서 확인
plugin:
  filePlugin: file_galtransl_json # auto면 입력 파일마다 자동 인식(여러 형식 혼합 가능). 자막 file_subtitle_srt_lrc_vtt, 소설 file_epub_epub 또는 file_plaintext_txt, 장면 TXT file_vn_scene_txt, mtool json은 file_i18n_json
  textPlugins: # 텍스트 처리 플러그인 목록. 여러 개를 순서대로 실행
    - text_common_normalfix # 일반 텍스트 수정 플러그인
    #- text_common_skipNoJP # 일본어 없는 문장 건너뛰기 플러그인
  problemPlugins: # 문제 검사 플러그인 목록. 순서대로 실행하며 []면 끔
    - problem_common # 일반 검사. 아래 problemAnalyze 설정 사용
  # 플러그인별 설정은 plugins 폴더의 yaml을 고치거나 여기에 쓸 수 있음:
  file_galtransl_json:
    output_with_src: False # gt_output에 원문을 함께 남길지[True/False]

# 프로그램 설정
common:
  gpt.numPerRequestTranslate: 16 # 요청당 문장 수. 16 이하 권장.[1-32]
  gpt.dynamicNumPerRequestTranslate: false # 동적 문장 수: 해석 오류에 따라 요청당 문장 수를 자동 조절.[True/False]
  gpt.dynamicNumPerRequestTranslate.min: 8 # 동적 조절의 최소 문장 수.[1-64]
  gpt.dynamicNumPerRequestTranslate.max: 64 # 동적 조절의 최대 문장 수.[1-64]
  workersPerProject: 16 # 프로젝트 단위 동시 처리 파일 수. 한 파일 안의 병렬 처리는 splitFile 필요.
  autoAdjustWorkers: false # 최근 429 비율과 응답 지연에 따라 동시 작업 수 자동 조절.[True/False]
  sortBy: "size" # 파일 처리 순서. name은 파일 이름순, size는 큰 파일 먼저(병렬 시 보통 더 빠름).[name/size]
  language: "ko" # 번역 결과 언어.[zh-cn/zh-tw/en/ja/ko/ru/fr]

  # 단일 파일 분할 설정
  ###【중요】분할 설정은 캐시 적중에 직접 영향을 줍니다. 옛 프로젝트를 옮길 때는 분할 설정을 같게 유지하세요 ###
  splitFile: "Num" # 단일 파일 분할 방식. no는 끔, Num은 n문장마다 자름, Equal은 파일마다 n조각으로 균등 분할.[no/Num/Equal]
  splitFileNum: 2048 # 분할 값. Num은 조각당 문장 수, Equal은 전체 조각 수.
  splitFileCrossNum: 0 # 조각 사이 겹침 문장 수(문맥 완충). 이어지는 부분의 품질이 좋아짐.[권장 0 또는 10]

  save_steps: 1 # n개 배치마다 캐시 저장. 값이 크면 덜 저장하고 조금 빨라질 수 있음.[1-999]
  start_time: "" # 예약 시작 시각(24시간 형식, 예 00:30). 비우면 바로 시작.[00:00-23:59]
  linebreakSymbol: "auto" # JSON 안의 줄바꿈 형식. 문제 검사/자동 수정에 쓰이며 번역 내용은 바꾸지 않음.
  skipH: false # 민감어 검출에 걸릴 수 있는 문장을 건너뛸지.[True/False]
  smartRetry: True # 해석에 실패하면 배치를 줄이고 문맥을 초기화해 쓸모없는 재시도를 줄임.[True/False]
  retranslFail: false # 다시 시작할 때 "(Failed)"로 표시된 문장을 자동으로 다시 번역할지.[True/False]
  retranslKey: # 다시 번역할 키워드. 원문/번역문/problem에 포함되면 재번역. 비우면 재번역 안 함.
    - "翻译失败" # 시작할 때 번역 실패(翻译失败) 문장을 다시 번역(기본 포함: 실패한 문장을 그대로 두지 않기 위함)
    #- "残留日文" # 시작할 때 일본어 잔류(残留日文) 문장을 다시 번역
  problemFilterKey: [] # 문제 필터(정규식). 일치하는 문제 항목은 표시·통계·problem 기준 재번역에서 제외. 원칙적으로 세부 항목만(예 "^残留日文：♪") 거르고 분류 전체는 거르지 말 것. 글자 그대로 거르려면 특수 문자를 이스케이프.
  problemWhiteList: [] # 문제 예외 목록. 「캐시 파일 이름:index」(예 a.json:12, 범위 a.json:12-15)로 항목을 예외 처리. 해당 항목의 skip_check를 켜는 것과 같음.

  gpt.contextNum: 8 # 요청마다 붙일 앞 문장 수. 클수록 문맥이 강하고 비용이 늘어남(보통 8).[0-32]
  # ForGal/ForGal-json/ForNovel
  gpt.translation_guideline: "JapaneseToKorean.md" # 사용할 번역 지침 파일 이름(translation_guidelines 폴더). 문체와 표현에 영향.
  gpt.enhance_jailbreak: False # 거절을 줄이는 보강 프롬프트 사용 여부.[True/False]
  # Sakura/GalTransl
  gpt.token_limit: 0 # (Sakura/GalTransl) 턴당 token 상한. 0은 제한 없음. 문맥 넘침을 막는 데 사용.
  # 디버그 로그
  loggingLevel: info # 로그 수준. debug는 상세, info는 일반, warning은 경고만.[debug/info/warning]
  saveLog: false # 로그를 파일로 저장할지.[True/False]



# 프록시 설정. 중계 서비스를 쓰면 보통 필요 없음
proxy:
  enableProxy: false # 프록시 사용 여부.[True/False]
  proxies:
    - address: http://127.0.0.1:7890

# 자동 문제 분석 설정. 문제 종류와 기본 사용 여부는 문제 플러그인이 정함
problemAnalyze:
  problemList: null # null은 플러그인 기본값, []는 모두 끔. 문제 이름 목록을 직접 쓸 수도 있음

# 사전 설정
dictionary:
  defaultDictFolder: Dict # 공통 사전 폴더. Windows는 프로그램 폴더, Linux는 사용자 데이터 폴더의 Dict. 절대 경로도 가능
  usePreDictInName: false # 번역 전 사전을 name 필드에 적용. name 필드 번역에 쓸 수 있으며 바뀐 name이 번역 엔진에 전달됨[True/False]
  usePostDictInName: false # 번역 후 사전을 name 필드에 적용[True/False]
  useGPTDictInName: true # GPT 사전을 name 필드에 적용[True/False]
  sortDict: true # 모든 사전을 찾을 말 길이순으로 다시 정렬.[True/False]
  # 번역 전 사전
  preDict:
    - (project_dir)项目字典_译前.txt # (project_dir)은 프로젝트 폴더의 사전
  # GPT 사전
  gpt.dict:
    - 공통GPT사전.txt
    - (project_dir)项目GPT字典.txt
    - (project_dir)项目GPT字典-生成.txt
  # 번역 후 사전
  postDict:
    - (project_dir)项目字典_译后.txt
"""
