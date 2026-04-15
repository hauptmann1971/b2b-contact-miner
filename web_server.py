from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import func, desc, text
from datetime import datetime
import sys
import os
import secrets

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, Keyword, SearchResult, DomainContact, Contact, CrawlLog, PipelineState, init_db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.route('/')
def index():
    """Главная страница с формой ввода ключевых слов и статистикой"""
    db = SessionLocal()
    try:
        # Получаем статистику
        total_keywords = db.query(Keyword).count()
        processed_keywords = db.query(Keyword).filter(Keyword.is_processed == True).count()
        total_domains = db.query(DomainContact).count()
        total_contacts = db.query(Contact).count()
        
        # Последние ключевые слова
        recent_keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).limit(10).all()
        
        # Статистика по типам контактов
        email_count = db.query(Contact).filter(Contact.contact_type == 'email').count()
        telegram_count = db.query(Contact).filter(Contact.contact_type == 'telegram').count()
        linkedin_count = db.query(Contact).filter(Contact.contact_type == 'linkedin').count()
        phone_count = db.query(Contact).filter(Contact.contact_type == 'phone').count()
        
        return render_template('index.html',
                             total_keywords=total_keywords,
                             processed_keywords=processed_keywords,
                             total_domains=total_domains,
                             total_contacts=total_contacts,
                             recent_keywords=recent_keywords,
                             email_count=email_count,
                             telegram_count=telegram_count,
                             linkedin_count=linkedin_count,
                             phone_count=phone_count)
    finally:
        db.close()


@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    """Добавление нового ключевого слова"""
    keyword_text = request.form.get('keyword', '').strip()
    language = request.form.get('language', 'ru')
    country = request.form.get('country', 'RU')
    
    # Валидация входных данных
    if not keyword_text:
        flash('Ключевое слово не может быть пустым', 'error')
        return redirect(url_for('index'))
    
    if len(keyword_text) > 500:
        flash('Ключевое слово слишком длинное (максимум 500 символов)', 'error')
        return redirect(url_for('index'))
    
    # Санитизация - удаляем потенциально опасные символы
    keyword_text = keyword_text.replace('<', '').replace('>', '').replace('"', '').replace("'", '')
    
    # Валидация языка и страны
    valid_languages = ['ru', 'en', 'kk', 'uz', 'ky', 'tg', 'az', 'hy', 'ka', 'be', 'ro']
    valid_countries = ['RU', 'KZ', 'UZ', 'KG', 'TJ', 'TM', 'AZ', 'AM', 'GE', 'BY', 'MD', 'UA', 'MN', 'AF', 'PK', 'US', 'GB', 'DE', 'FR']
    
    if language not in valid_languages:
        language = 'ru'  # Значение по умолчанию
    
    if country not in valid_countries:
        country = 'RU'  # Значение по умолчанию
    
    db = SessionLocal()
    try:
        # Проверяем, существует ли уже такое ключевое слово
        existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        if existing:
            flash(f'Ключевое слово "{keyword_text}" уже существует', 'warning')
            return redirect(url_for('index'))
        
        # Создаем новое ключевое слово
        new_keyword = Keyword(
            keyword=keyword_text,
            language=language,
            country=country,
            is_processed=False
        )
        db.add(new_keyword)
        db.commit()
        
        flash(f'Ключевое слово "{keyword_text}" успешно добавлено!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при добавлении: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()


@app.route('/keywords')
def keywords_list():
    """Список всех ключевых слов"""
    db = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        keywords_query = db.query(Keyword).order_by(desc(Keyword.created_at))
        total = keywords_query.count()
        keywords = keywords_query.offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('keywords.html', 
                             keywords=keywords, 
                             page=page, 
                             per_page=per_page, 
                             total=total)
    finally:
        db.close()


@app.route('/keyword/<int:keyword_id>')
def keyword_detail(keyword_id):
    """Детальная информация о ключевом слове"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            flash('Ключевое слово не найдено', 'error')
            return redirect(url_for('keywords_list'))
        
        # Получаем результаты поиска
        search_results = db.query(SearchResult).filter(
            SearchResult.keyword_id == keyword_id
        ).order_by(SearchResult.position).all()
        
        # Получаем домены и контакты
        domain_contacts = []
        for sr in search_results:
            domains = db.query(DomainContact).filter(
                DomainContact.search_result_id == sr.id
            ).all()
            for domain in domains:
                contacts = db.query(Contact).filter(
                    Contact.domain_contact_id == domain.id
                ).all()
                domain_contacts.append({
                    'domain': domain,
                    'contacts': contacts,
                    'search_result': sr
                })
        
        return render_template('keyword_detail.html',
                             keyword=keyword,
                             search_results=search_results,
                             domain_contacts=domain_contacts)
    finally:
        db.close()


@app.route('/contacts')
def contacts_list():
    """Список всех найденных контактов"""
    db = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        contact_type = request.args.get('type', '')
        
        contacts_query = db.query(Contact).join(DomainContact).join(SearchResult).join(Keyword)
        
        if contact_type:
            contacts_query = contacts_query.filter(Contact.contact_type == contact_type)
        
        contacts_query = contacts_query.order_by(desc(Contact.created_at))
        total = contacts_query.count()
        contacts = contacts_query.offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('contacts.html',
                             contacts=contacts,
                             page=page,
                             per_page=per_page,
                             total=total,
                             selected_type=contact_type)
    finally:
        db.close()


@app.route('/health-check')
def health_check_page():
    """Страница health check с визуальным интерфейсом"""
    return render_template('health.html')


@app.route('/api-docs')
def api_docs_page():
    """Страница документации API"""
    return render_template('api_docs.html')


@app.route('/delete_keyword/<int:keyword_id>', methods=['POST'])
def delete_keyword(keyword_id):
    """Удаление ключевого слова"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            flash(f'Ключевое слово "{keyword.keyword}" удалено', 'success')
        else:
            flash('Ключевое слово не найдено', 'error')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    finally:
        db.close()
    
    return redirect(url_for('keywords_list'))


# Health Check Endpoints
@app.route('/health')
def health_check():
    """Полная проверка здоровья системы"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {}
    }
    
    # Проверка базы данных
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
    
    # Проверка Redis (если настроен)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
        r.ping()
        health_status['services']['redis'] = 'healthy'
    except Exception:
        health_status['services']['redis'] = 'unhealthy'
    
    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503


@app.route('/health/live')
def liveness_check():
    """Проверка живости приложения"""
    return jsonify({'status': 'alive', 'timestamp': datetime.utcnow().isoformat()}), 200


@app.route('/health/ready')
def readiness_check():
    """Проверка готовности приложения"""
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        return jsonify({'status': 'ready', 'timestamp': datetime.utcnow().isoformat()}), 200
    except Exception as e:
        return jsonify({'status': 'not_ready', 'error': str(e)}), 503


@app.route('/api/stats')
def api_stats():
    """API эндпоинт для получения статистики"""
    db = SessionLocal()
    try:
        stats = {
            'total_keywords': db.query(Keyword).count(),
            'processed_keywords': db.query(Keyword).filter(Keyword.is_processed == True).count(),
            'total_domains': db.query(DomainContact).count(),
            'total_contacts': db.query(Contact).count(),
            'contacts_by_type': {
                'email': db.query(Contact).filter(Contact.contact_type == 'email').count(),
                'telegram': db.query(Contact).filter(Contact.contact_type == 'telegram').count(),
                'linkedin': db.query(Contact).filter(Contact.contact_type == 'linkedin').count(),
                'phone': db.query(Contact).filter(Contact.contact_type == 'phone').count()
            }
        }
        return jsonify(stats)
    finally:
        db.close()


@app.route('/api/keywords')
def api_keywords():
    """API эндпоинт для получения списка ключевых слов"""
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).all()
        return jsonify([{
            'id': k.id,
            'keyword': k.keyword,
            'language': k.language,
            'country': k.country,
            'is_processed': k.is_processed,
            'last_crawled_at': k.last_crawled_at.isoformat() if k.last_crawled_at else None,
            'created_at': k.created_at.isoformat()
        } for k in keywords])
    finally:
        db.close()


if __name__ == '__main__':
    # Инициализация базы данных
    init_db()
    
    # Запуск Flask сервера
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
