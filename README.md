# Chirp3 음성 합성(ICV/HD) 테스트 및 비교

## 1. 프로젝트 개요

이 프로젝트는 Google Cloud의 Text-to-Speech API, 특히 최신 음성 모델인 **Chirp3**를 활용하는 웹 애플리케이션입니다. 사용자는 이 애플리케이션을 통해 두 가지 주요 음성 합성 방식을 테스트하고 그 결과를 비교해볼 수 있습니다.

- **ICV (Instant Custom Voice):** 사용자가 제공한 짧은 음성 샘플을 기반으로 즉석에서 개인화된 목소리를 복제하여 음성을 생성합니다.
- **HD (High-Definition):** Google이 사전 학습한 고품질의 표준 음성 모델을 사용하여 음성을 생성합니다.

사용자는 웹 인터페이스에 텍스트를 입력하고, 두 가지 모델로 생성된 음성을 직접 들어보며 합성 속도와 음성 품질을 직관적으로 비교할 수 있습니다.

## 2. 주요 기능

- **웹 기반 인터페이스:** 사용자가 쉽게 텍스트를 입력하고 결과를 확인할 수 있는 UI 제공.
- **실시간 음성 합성:** 입력된 텍스트를 ICV와 HD 두 가지 모드로 동시에 합성.
- **음성 비교 및 재생:** 생성된 두 음성을 웹에서 즉시 재생하고 들어볼 수 있음.
- **성능 비교:** 각 음성의 합성 소요 시간을 측정하여 어떤 모델이 더 빨랐는지 시각적으로 표시.
- **클라우드 네이티브:** Docker 컨테이너 기반으로 Google Cloud Run에 쉽게 배포하고 확장 가능.

## 3. 아키텍처

이 애플리케이션은 다음과 같은 간단한 클라우드 기반 아키텍처로 구성됩니다.

```
[사용자] --- HTTPS ---> [Google Cloud Run] ---> [Google Text-to-Speech API]
   |                      (Flask/Gunicorn)           |
   |                                                 |
   +-------------------------------------------------+
   (생성된 음성 파일 재생)
```

1.  **사용자:** 웹 브라우저를 통해 Cloud Run에 배포된 서비스 URL에 접속합니다.
2.  **Google Cloud Run:** 사용자의 요청을 받아 Flask 웹 서버가 처리합니다.
    -   `app.py`는 사용자가 입력한 텍스트를 Google Text-to-Speech API로 전달합니다.
    -   이때, ICV(복제 음성)와 HD(표준 음성) 두 가지 방식으로 각각 요청을 보냅니다.
3.  **Google Text-to-Speech API:** 요청을 받아 음성을 합성하고, 오디오 데이터를 반환합니다.
4.  **결과 반환:** Cloud Run은 생성된 오디오를 사용자에게 전달하여 웹 인터페이스에서 재생할 수 있도록 합니다.

## 4. 디렉토리 구조

```
.
├── static/               # 생성된 오디오 파일 임시 저장
│   └── (생성된 .wav 파일들)
├── templates/            # Flask HTML 템플릿
│   └── index.html
├── .gitignore            # Git 추적 제외 파일 목록
├── app.py                # Flask 웹 애플리케이션 로직
├── consent.wav           # 음성 복제 동의 녹음 파일 (필수)
├── Dockerfile            # Cloud Run 배포를 위한 컨테이너 설정
├── README.md             # 프로젝트 설명 (현재 파일)
├── reference.wav         # 음성 복제를 위한 참조 녹음 파일 (필수)
├── requirements.txt      # Python 패키지 의존성 목록
└── voice_key.txt         # 생성된 음성 복제 키 (배포 시 포함)
```

## 5. 로컬 환경 설정 및 실행

### 5.1. 사전 준비

-   Python 3.8 이상 설치
-   Google Cloud SDK (`gcloud` CLI) 설치 및 초기 설정 완료
-   음성 복제를 위한 오디오 파일 준비:
    -   `reference.wav`: 복제할 목소리가 녹음된 10초 내외의 샘플 오디오
    -   `consent.wav`: 음성 제공자가 복제에 동의한다는 내용의 10초 내외의 오디오

### 5.2. 설정 단계

1.  **저장소 복제**
    ```bash
    git clone https://github.com/ldu1225/chirp3_icv_hd_tts_test.git
    cd chirp3_icv_hd_tts_test
    ```

2.  **Python 가상 환경 생성 및 활성화**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **필요한 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Google Cloud 인증**
    로컬 환경에서 Google Cloud API를 사용하기 위해 애플리케이션 기본 인증을 수행합니다.
    ```bash
    gcloud auth application-default login
    ```

5.  **음성 복제 키 생성 (`voice_key.txt`)**
    ICV 음성을 사용하기 위해서는 고유한 음성 키가 필요합니다. 이 키는 `reference.wav`와 `consent.wav` 파일을 기반으로 생성됩니다.
    
    **중요:** `app.py`는 실행 시 `voice_key.txt` 파일이 없으면 오류가 발생합니다. 아래의 임시 스크립트를 사용하여 키를 먼저 생성해야 합니다.

    -   `generate_key.py` 라는 임시 파일을 프로젝트 루트에 만듭니다. (내용은 이전 대화 기록 참고)
    -   아래 명령어로 스크립트를 실행하여 `voice_key.txt` 파일을 생성합니다.
    ```bash
    python3 generate_key.py
    ```
    -   성공적으로 `voice_key.txt`가 생성되면 `generate_key.py` 파일은 삭제해도 됩니다.

6.  **로컬 웹 서버 실행**
    ```bash
    python3 app.py
    ```
    서버가 실행되면 웹 브라우저에서 `http://localhost:8080` 주소로 접속하여 테스트할 수 있습니다.

## 6. Google Cloud Run 배포

1.  **사전 준비**
    -   로컬 환경 설정이 완료되고, `voice_key.txt` 파일이 생성되어 있어야 합니다.
    -   배포하려는 Google Cloud 프로젝트에서 Cloud Run API와 Cloud Build API가 활성화되어 있어야 합니다.

2.  **배포 명령어 실행**
    프로젝트 루트 디렉토리에서 아래의 `gcloud` 명령어를 실행합니다. `<YOUR_GCP_PROJECT_ID>` 부분을 실제 프로젝트 ID로 변경해주세요.

    ```bash
    gcloud run deploy chirp3-tts-comparison \
      --source . \
      --region asia-northeast3 \
      --allow-unauthenticated \
      --project=<YOUR_GCP_PROJECT_ID> \
      --quiet
    ```
    -   `--source .`: 현재 디렉토리의 소스를 사용하여 배포합니다.
    -   `--region asia-northeast3`: 서울 리전에 배포합니다. (원하는 리전으로 변경 가능)
    -   `--allow-unauthenticated`: 인증 없이 누구나 서비스에 접근할 수 있도록 허용합니다.
    -   `--quiet`: 배포 중 나타나는 모든 프롬프트에 자동으로 'yes'로 응답합니다.

3.  **배포 확인**
    배포가 성공적으로 완료되면, 명령어 출력 마지막에 **Service URL**이 표시됩니다. 이 URL을 통해 누구나 웹 애플리케이션에 접속할 수 있습니다.

## 7. 주요 파일 설명

-   **`app.py`**: Flask를 사용한 메인 웹 애플리케이션입니다. 사용자의 요청을 받아 TTS API와 통신하고 결과를 반환합니다.
-   **`Dockerfile`**: Cloud Run 배포를 위한 컨테이너 이미지 빌드 방법을 정의합니다. Python 환경 설정, 의존성 설치, Gunicorn 서버 실행 명령이 포함됩니다.
-   **`requirements.txt`**: 프로젝트에 필요한 Python 라이브러리 목록입니다.
-   **`templates/index.html`**: 사용자가 보는 웹페이지의 구조와 디자인을 담고 있는 HTML 파일입니다.
-   **`voice_key.txt`**: ICV 음성 합성에 사용되는 고유 키입니다. 이 파일이 없으면 커스텀 음성을 생성할 수 없으므로, 배포 시 반드시 소스 코드에 포함되어야 합니다.
