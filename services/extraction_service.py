import re
from typing import List, Dict, Optional
from email_validator import validate_email, EmailNotValidError
from config.settings import settings
from loguru import logger
from models.schemas import ContactInfo


class ExtractionService:
    def __init__(self):
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.mailto_pattern = re.compile(r'href=["\']mailto:([^"\']+)["\']', re.IGNORECASE)
        
        # Telegram patterns
        self.telegram_pattern = re.compile(r'(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)')
        self.telegram_at_pattern = re.compile(r'(?:Telegram|TG|Телеграм)[:\s]*@([a-zA-Z0-9_]{5,})', re.IGNORECASE)
        self.telegram_join_pattern = re.compile(r'join\.chat/([A-Za-z0-9_-]+)')
        
        # LinkedIn patterns
        self.linkedin_pattern = re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|company)/([a-zA-Z0-9_-]+)')
        self.linkedin_text_pattern = re.compile(r'LinkedIn[:\s]*(?:https?://)?(?:www\.)?linkedin\.com/(?:in|company)/([a-zA-Z0-9_-]+)', re.IGNORECASE)
        
        self.phone_pattern = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        
        self.obfuscation_patterns = [
            r'\[at\]', r'\(at\)', r' at ',
            r'\[dot\]', r'\(dot\)', r' dot ',
            r'{@}', r' {@} ',
        ]
    
    def extract_contacts(self, content_list: List[Dict]) -> tuple:
        """Extract contacts with smart LLM fallback
        Returns: (ContactInfo, llm_data) where llm_data is dict with request/response/model or None
        """
        emails = set()
        telegram_links = set()
        linkedin_links = set()
        phone_numbers = set()
        
        needs_llm_fallback = False
        llm_candidate_pages = []
        llm_data = None  # Will store {request, response, model} if LLM used
        
        for item in content_list:
            content = item.get("content", "")
            url = item.get("url", "")
            page_type = item.get("type", "")
            
            found_emails = self.email_pattern.findall(content)
            for email in found_emails:
                if self._is_valid_business_email(email):
                    emails.add(email.lower())
            
            mailto_matches = self.mailto_pattern.finditer(content)
            for match in mailto_matches:
                email = match.group(1).strip()
                email = email.split('?')[0]
                if self._is_valid_business_email(email):
                    emails.add(email.lower())
            
            has_obfuscation = any(re.search(pattern, content, re.IGNORECASE) 
                                 for pattern in self.obfuscation_patterns)
            
            telegram_matches = self.telegram_pattern.finditer(content)
            for match in telegram_matches:
                telegram_links.add(f"https://t.me/{match.group(1)}")
            
            # Also check for @username mentions after Telegram keyword
            telegram_at_matches = self.telegram_at_pattern.finditer(content)
            for match in telegram_at_matches:
                username = match.group(1)
                telegram_links.add(f"https://t.me/{username}")
            
            # Check for t.me links in href attributes
            telegram_href = re.findall(r'href=["\']([^"\']*t\.me[^"\']*)["\']', content)
            for link in telegram_href:
                telegram_links.add(link)
            
            # Check for join.chat links
            join_chat_matches = self.telegram_join_pattern.finditer(content)
            for match in join_chat_matches:
                telegram_links.add(f"https://join.chat/{match.group(1)}")
            
            linkedin_matches = self.linkedin_pattern.finditer(content)
            for match in linkedin_matches:
                full_url = f"https://linkedin.com/in/{match.group(1)}" if '/' not in match.group(1) else match.group(0)
                linkedin_links.add(full_url)
            
            # Also check LinkedIn text patterns
            linkedin_text_matches = self.linkedin_text_pattern.finditer(content)
            for match in linkedin_text_matches:
                profile_id = match.group(1)
                linkedin_links.add(f"https://linkedin.com/in/{profile_id}")
            
            phones = self.phone_pattern.findall(content)
            for phone in phones:
                cleaned = re.sub(r'[^\d+]', '', phone)
                if len(cleaned) >= 10:
                    phone_numbers.add(phone)
            
            if page_type == "contact_page" and has_obfuscation and len(emails) < 2:
                llm_candidate_pages.append(content[:3000])
                needs_llm_fallback = True
        
        if needs_llm_fallback and settings.USE_LLM_EXTRACTION:
            logger.info(f"Applying LLM fallback for {len(llm_candidate_pages)} pages with obfuscated emails")
            llm_contacts, llm_data = self._extract_with_llm_selective(llm_candidate_pages)
            
            emails.update(llm_contacts.emails)
            telegram_links.update(llm_contacts.telegram_links)
            linkedin_links.update(llm_contacts.linkedin_links)
        
        filtered_emails = self._filter_blocked_emails(list(emails))
        
        logger.info(f"Extracted: {len(filtered_emails)} emails, {len(telegram_links)} Telegram, {len(linkedin_links)} LinkedIn")
        
        return ContactInfo(
            emails=filtered_emails,
            telegram_links=list(telegram_links),
            linkedin_links=list(linkedin_links),
            phone_numbers=list(phone_numbers)
        ), llm_data
    
    def _extract_with_llm_selective(self, obfuscated_contents: List[str]) -> tuple:
        """Use LLM only for pages with obfuscated emails
        Returns: (ContactInfo, llm_data) where llm_data has request/response/model
        """
        # Determine which LLM to use (priority: YandexGPT > GigaChat > DeepSeek > OpenAI)
        if settings.USE_YANDEXGPT and settings.YANDEX_IAM_TOKEN and settings.YANDEX_FOLDER_ID:
            llm_type = "yandexgpt"
        elif settings.USE_GIGACHAT and settings.GIGACHAT_CLIENT_ID and settings.GIGACHAT_CLIENT_SECRET:
            llm_type = "gigachat"
        elif settings.USE_DEEPSEEK and settings.DEEPSEEK_API_KEY:
            llm_type = "deepseek"
        elif settings.USE_OPENAI and settings.OPENAI_API_KEY:
            llm_type = "openai"
        else:
            return ContactInfo(), None
        
        try:
            combined_content = "\n\n--- PAGE SEPARATOR ---\n\n".join(obfuscated_contents)
            
            prompt = f"""
Extract contact information from the following website content.

IMPORTANT RULES:
1. Return ONLY valid JSON, no additional text
2. Look for obfuscated emails like: name[at]domain.com, name (at) domain (dot) com
3. Find ALL Telegram contacts:
   - Links: t.me/username, telegram.me/username, join.chat/GROUP
   - Mentions: "Telegram: @username", "TG: @username", "@username"
4. Find ALL LinkedIn profiles:
   - Personal: linkedin.com/in/name
   - Company: linkedin.com/company/name
   - Any mention of LinkedIn with URL
5. Exclude generic emails: noreply@, support@, admin@, webmaster@
6. Include business emails even if they are info@ or sales@
7. Look for phone numbers in any format

Content to analyze:
{combined_content[:4000]}

Return EXACTLY this JSON format (no extra text before or after):
{{
  "emails": ["email1@example.com", "email2@example.com"],
  "telegram": ["https://t.me/username", "@username", "https://join.chat/GROUP"],
  "linkedin": ["https://linkedin.com/in/name", "https://linkedin.com/company/name"]
}}

If no contacts found, return:
{{"emails": [], "telegram": [], "linkedin": []}}
            """
            
            # Call appropriate LLM
            if llm_type == "yandexgpt":
                import requests
                import json
                
                url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
                
                headers = {
                    "Content-Type": "application/json",
                    "x-folder-id": settings.YANDEX_FOLDER_ID
                }
                
                # Use IAM token or API key
                if settings.YANDEX_IAM_TOKEN and settings.YANDEX_IAM_TOKEN != "your_yandex_iam_token":
                    headers["Authorization"] = f"Bearer {settings.YANDEX_IAM_TOKEN}"
                else:
                    # Fallback to API key (if provided)
                    raise Exception("YANDEX_IAM_TOKEN is required for YandexGPT")
                
                payload = {
                    "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.1,
                        "maxTokens": "300"
                    },
                    "messages": [
                        {"role": "user", "text": prompt}
                    ]
                }
                
                # Store request data
                llm_request_data = {
                    "prompt": prompt[:2000],  # Truncate for storage
                    "payload": str(payload)[:2000]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                content = result["result"]["alternatives"][0]["message"]["text"]
                
                # Store response data
                llm_response_data = {
                    "response": content,
                    "full_result": str(result)[:2000]
                }
                
            elif llm_type == "gigachat":
                from gigachat import GigaChat
                
                gc = GigaChat(
                    credentials=settings.GIGACHAT_CLIENT_ID,
                    client_secret=settings.GIGACHAT_CLIENT_SECRET,
                    verify_ssl_certs=False,
                    scope="GIGACHAT_API_PERS"
                )
                
                # Store request data
                llm_request_data = {
                    "prompt": prompt[:2000],
                    "model": "gigachat"
                }
                
                response = gc.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300
                )
                
                content = response.choices[0].message.content
                
                # Store response data
                llm_response_data = {
                    "response": content
                }
                
            elif llm_type == "deepseek":
                from openai import OpenAI
                client = OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com/v1"
                )
                
                # Store request data
                llm_request_data = {
                    "prompt": prompt[:2000],
                    "model": "deepseek-chat"
                }
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300
                )
                content = response.choices[0].message.content
                
                # Store response data
                llm_response_data = {
                    "response": content
                }
                
            else:  # openai
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Store request data
                llm_request_data = {
                    "prompt": prompt[:2000],
                    "model": "gpt-3.5-turbo"
                }
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300
                )
                content = response.choices[0].message.content
                
                # Store response data
                llm_response_data = {
                    "response": content
                }
            
            import json
            try:
                extracted = json.loads(content)
                logger.debug(f"LLM response (first 300 chars): {content[:300]}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from LLM, attempting to fix: {e}")
                logger.warning(f"LLM response (first 500 chars): {content[:500]}")
                
                # Try to extract JSON from response
                try:
                    # Look for JSON object in the response
                    import re
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        extracted = json.loads(json_str)
                        logger.info("Successfully extracted JSON from LLM response")
                        logger.debug(f"Extracted JSON: {json_str[:200]}")
                    else:
                        logger.error("Could not find JSON in LLM response")
                        return ContactInfo(), None
                except Exception as fix_error:
                    logger.error(f"Failed to fix JSON: {fix_error}")
                    return ContactInfo(), None
            
            # Валидация структуры ответа
            if not isinstance(extracted, dict):
                logger.error(f"LLM returned non-dict response: {type(extracted)}")
                return ContactInfo(), None
            
            # Prepare LLM data for storage
            llm_data = {
                "request": str(llm_request_data),
                "response": str(llm_response_data),
                "model": llm_type
            }
            
            return ContactInfo(
                emails=extracted.get("emails", []),
                telegram_links=extracted.get("telegram", []),
                linkedin_links=extracted.get("linkedin", []),
                phone_numbers=[]
            ), llm_data
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return ContactInfo(), None
    
    def verify_mx_domain(self, email: str) -> bool:
        """Check if email domain has MX records (DNS verification)"""
        try:
            import dns.resolver
            domain = email.split('@')[1]
            records = dns.resolver.resolve(domain, 'MX')
            return len(records) > 0
        except Exception as e:
            logger.debug(f"MX verification failed for {email}: {e}")
            return False
    
    async def batch_verify_emails(self, emails: List[str]) -> Dict[str, bool]:
        """Batch verify multiple emails via MX records"""
        results = {}
        for email in emails:
            is_valid = self.verify_mx_domain(email)
            results[email] = is_valid
            logger.debug(f"Email {email}: MX {'valid' if is_valid else 'invalid'}")
        return results
    
    def _is_valid_business_email(self, email: str) -> bool:
        """Validate email format"""
        try:
            valid = validate_email(email)
            email_lower = email.lower()
            
            for pattern in settings.BLOCKED_EMAIL_PATTERNS:
                if re.match(pattern, email_lower):
                    return False
            
            free_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'mail.ru', 'yandex.ru']
            domain = email_lower.split('@')[1]
            if domain in free_providers:
                return False
            
            return True
        except EmailNotValidError:
            return False
    
    def _filter_blocked_emails(self, emails: List[str]) -> List[str]:
        """Remove blocked emails"""
        return [email for email in emails if self._is_valid_business_email(email)]
    
    def calculate_confidence(self, contacts: ContactInfo) -> int:
        """Calculate confidence score"""
        score = 0
        
        if len(contacts.emails) > 0:
            score += 40
            if len(contacts.emails) > 1:
                score += 10
        
        if len(contacts.telegram_links) > 0:
            score += 25
        
        if len(contacts.linkedin_links) > 0:
            score += 25
        
        if len(contacts.phone_numbers) > 0:
            score += 10
        
        return min(score, 100)
