import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class FirebaseService:
    def __init__(self):
        """Firebase 서비스 초기화"""
        self.db = None
        self.collection_name = os.getenv('FIREBASE_COLLECTION_NAME', 'notices')
        self.initialized = False
        
        try:
            self._initialize_firebase()
        except Exception as e:
            logging.error(f"Firebase 초기화 실패: {e}")
    
    def _initialize_firebase(self):
        """Firebase 초기화"""
        if os.getenv('ENABLE_FIREBASE_SYNC', 'false').lower() != 'true':
            logging.info("Firebase 동기화가 비활성화되어 있습니다.")
            return
        
        # Firebase 설정 정보
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
        }
        
        # 필수 설정 확인
        required_fields = ['project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        
        if missing_fields:
            logging.error(f"Firebase 설정이 불완전합니다. 누락된 필드: {missing_fields}")
            return
        
        try:
            # Firebase 앱이 이미 초기화되었는지 확인
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.initialized = True
            logging.info("Firebase 초기화 성공")
            
        except Exception as e:
            logging.error(f"Firebase 초기화 중 오류 발생: {e}")
            self.initialized = False
    
    def is_initialized(self) -> bool:
        """Firebase가 초기화되었는지 확인"""
        return self.initialized and self.db is not None
    
    async def save_notice(self, notice_data: Dict[str, Any]) -> Optional[str]:
        """단일 공지사항을 Firebase에 저장"""
        if not self.is_initialized():
            logging.warning("Firebase가 초기화되지 않았습니다.")
            return None
        
        try:
            # Firebase에 저장할 데이터 준비
            firebase_data = {
                'category': notice_data.get('category', ''),
                'number': notice_data.get('number', ''),
                'title': notice_data.get('title', ''),
                'author': notice_data.get('author', ''),
                'date': notice_data.get('date', ''),
                'attachments': notice_data.get('attachments', ''),
                'views': notice_data.get('views', ''),
                'url': notice_data.get('url', ''),
                'content': notice_data.get('content', ''),
                'content_html': notice_data.get('content_html', ''),
                'image_urls': notice_data.get('image_urls', []),
                'crawled_at': notice_data.get('crawled_at', ''),
                'firebase_created_at': datetime.now().isoformat(),
                'firebase_updated_at': datetime.now().isoformat()
            }
            
            # URL을 기반으로 문서 ID 생성 (중복 방지)
            doc_id = self._generate_doc_id(notice_data)
            
            # 기존 문서 확인
            doc_ref = self.db.collection(self.collection_name).document(doc_id)
            existing_doc = doc_ref.get()
            
            if existing_doc.exists:
                # 기존 문서가 있으면 업데이트
                firebase_data['firebase_updated_at'] = datetime.now().isoformat()
                doc_ref.update(firebase_data)
                logging.info(f"Firebase 문서 업데이트: {doc_id}")
            else:
                # 새 문서 생성
                doc_ref.set(firebase_data)
                logging.info(f"Firebase 새 문서 생성: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            logging.error(f"Firebase 저장 실패 ({notice_data.get('title', 'N/A')}): {e}")
            return None
    
    async def save_notices_batch(self, notices_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """여러 공지사항을 배치로 Firebase에 저장"""
        if not self.is_initialized():
            logging.warning("Firebase가 초기화되지 않았습니다.")
            return {'success': 0, 'failed': len(notices_data), 'details': []}
        
        success_count = 0
        failed_count = 0
        details = []
        
        # Firestore 배치 작업 사용
        batch = self.db.batch()
        batch_count = 0
        max_batch_size = 500  # Firestore 배치 제한
        
        try:
            for notice_data in notices_data:
                try:
                    firebase_data = {
                        'category': notice_data.get('category', ''),
                        'number': notice_data.get('number', ''),
                        'title': notice_data.get('title', ''),
                        'author': notice_data.get('author', ''),
                        'date': notice_data.get('date', ''),
                        'attachments': notice_data.get('attachments', ''),
                        'views': notice_data.get('views', ''),
                        'url': notice_data.get('url', ''),
                        'content': notice_data.get('content', ''),
                        'content_html': notice_data.get('content_html', ''),
                        'image_urls': notice_data.get('image_urls', []),
                        'crawled_at': notice_data.get('crawled_at', ''),
                        'firebase_created_at': datetime.now().isoformat(),
                        'firebase_updated_at': datetime.now().isoformat()
                    }
                    
                    doc_id = self._generate_doc_id(notice_data)
                    doc_ref = self.db.collection(self.collection_name).document(doc_id)
                    
                    # 기존 문서 확인
                    existing_doc = doc_ref.get()
                    if existing_doc.exists:
                        firebase_data['firebase_updated_at'] = datetime.now().isoformat()
                        batch.update(doc_ref, firebase_data)
                    else:
                        batch.set(doc_ref, firebase_data)
                    
                    batch_count += 1
                    details.append({
                        'doc_id': doc_id,
                        'title': notice_data.get('title', 'N/A')[:50],
                        'status': 'pending'
                    })
                    
                    # 배치 크기 제한 체크
                    if batch_count >= max_batch_size:
                        batch.commit()
                        logging.info(f"Firebase 배치 커밋: {batch_count}개 문서")
                        batch = self.db.batch()
                        batch_count = 0
                        
                except Exception as e:
                    logging.error(f"배치 처리 중 오류 ({notice_data.get('title', 'N/A')}): {e}")
                    failed_count += 1
                    details.append({
                        'title': notice_data.get('title', 'N/A')[:50],
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 남은 배치 커밋
            if batch_count > 0:
                batch.commit()
                logging.info(f"Firebase 최종 배치 커밋: {batch_count}개 문서")
            
            success_count = len(notices_data) - failed_count
            
            logging.info(f"Firebase 배치 저장 완료: 성공 {success_count}개, 실패 {failed_count}개")
            
        except Exception as e:
            logging.error(f"Firebase 배치 저장 중 오류: {e}")
            failed_count = len(notices_data)
            success_count = 0
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(notices_data),
            'details': details
        }
    
    def _generate_doc_id(self, notice_data: Dict[str, Any]) -> str:
        """공지사항 데이터를 기반으로 고유 문서 ID 생성"""
        category = notice_data.get('category', 'unknown')
        number = notice_data.get('number', '0')
        url = notice_data.get('url', '')
        
        # URL 해시를 사용하여 고유 ID 생성
        url_hash = str(abs(hash(url))) if url else str(abs(hash(category + number)))
        return f"{category}_{number}_{url_hash}"
    
    async def get_notice_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Firebase에서 특정 공지사항 조회"""
        if not self.is_initialized():
            return None
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc_id
                return data
            return None
            
        except Exception as e:
            logging.error(f"Firebase 문서 조회 실패 ({doc_id}): {e}")
            return None
    
    async def search_notices(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Firebase에서 공지사항 검색"""
        if not self.is_initialized():
            return []
        
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # 카테고리 필터
            if category:
                collection_ref = collection_ref.where('category', '==', category)
            
            # 최신순 정렬
            collection_ref = collection_ref.order_by('firebase_created_at', direction=firestore.Query.DESCENDING)
            
            # 제한
            if limit:
                collection_ref = collection_ref.limit(limit)
            
            docs = collection_ref.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # 검색어 필터링 (제목과 내용에서 검색)
                title = data.get('title', '').lower()
                content = data.get('content', '').lower()
                query_lower = query.lower()
                
                if query_lower in title or query_lower in content:
                    results.append(data)
            
            return results
            
        except Exception as e:
            logging.error(f"Firebase 검색 실패: {e}")
            return []
    
    async def get_notices_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Firebase에서 카테고리별 공지사항 조회"""
        if not self.is_initialized():
            return []
        
        try:
            collection_ref = self.db.collection(self.collection_name)
            collection_ref = collection_ref.where('category', '==', category)
            collection_ref = collection_ref.order_by('firebase_created_at', direction=firestore.Query.DESCENDING)
            
            if limit:
                collection_ref = collection_ref.limit(limit)
            
            docs = collection_ref.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logging.error(f"Firebase 카테고리 조회 실패 ({category}): {e}")
            return []
    
    async def get_latest_notices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Firebase에서 최신 공지사항 조회"""
        if not self.is_initialized():
            return []
        
        try:
            collection_ref = self.db.collection(self.collection_name)
            collection_ref = collection_ref.order_by('firebase_created_at', direction=firestore.Query.DESCENDING)
            collection_ref = collection_ref.limit(limit)
            
            docs = collection_ref.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logging.error(f"Firebase 최신 공지사항 조회 실패: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Firebase 컬렉션 통계 정보 조회"""
        if not self.is_initialized():
            return {}
        
        try:
            # 전체 문서 수
            total_docs = len(list(self.db.collection(self.collection_name).stream()))
            
            # 카테고리별 통계
            categories = {}
            docs = self.db.collection(self.collection_name).stream()
            
            for doc in docs:
                data = doc.to_dict()
                category = data.get('category', 'Unknown')
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            # 최근 업데이트 시간
            latest_doc = self.db.collection(self.collection_name)\
                .order_by('firebase_updated_at', direction=firestore.Query.DESCENDING)\
                .limit(1)\
                .stream()
            
            latest_update = None
            for doc in latest_doc:
                data = doc.to_dict()
                latest_update = data.get('firebase_updated_at')
                break
            
            return {
                'total_documents': total_docs,
                'categories': categories,
                'latest_update': latest_update,
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logging.error(f"Firebase 통계 조회 실패: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Firebase 연결 테스트"""
        if not self.is_initialized():
            return False
        
        try:
            # 간단한 쿼리로 연결 테스트
            collection_ref = self.db.collection(self.collection_name)
            list(collection_ref.limit(1).stream())
            logging.info("Firebase 연결 테스트 성공")
            return True
        except Exception as e:
            logging.error(f"Firebase 연결 테스트 실패: {e}")
            return False
    
    def cleanup(self):
        """Firebase 연결 정리"""
        try:
            if hasattr(self, 'db') and self.db:
                # Firebase 연결은 자동으로 관리되므로 특별한 정리 작업은 필요하지 않음
                logging.info("Firebase 연결 정리 완료")
            else:
                logging.info("Firebase 연결이 없어 정리할 필요가 없습니다")
        except Exception as e:
            logging.error(f"Firebase 연결 정리 중 오류: {e}")

