import sqlite3
from flask import Flask, request, jsonify, render_template, g
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
DATABASE = 'db/jobs.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def insert_job(title, company, salary, experience, city):
    db = get_db()
    db.execute('INSERT INTO jobs (title, company, salary, experience, city) VALUES (?, ?, ?, ?, ?)',
               [title, company, salary, experience, city])
    db.commit()

def parse_hh_ru(job_title, city, company):
    jobs = []
    url = f'https://hh.ru/search/vacancy?text={job_title}&area={city}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for item in soup.find_all('div', class_='vacancy-serp-item'):
        title_elem = item.find('a', class_='bloko-link')
        comp_elem = item.find('div', class_='vacancy-serp-item__meta-info-company')
        salary_elem = item.find('div', class_='vacancy-serp-item__sidebar')
        exp_elem = item.find('div', class_='vacancy-serp-item__info')
        location_elem = item.find('span', class_='vacancy-serp-item__meta-info')

        title = title_elem.text if title_elem else 'Не указано'
        comp = comp_elem.text.strip() if comp_elem else 'Не указано'
        salary = salary_elem.text.strip() if salary_elem else 'Не указано'
        exp = exp_elem.text.strip() if exp_elem else 'Не указано'
        location = location_elem.text.strip() if location_elem else 'Не указано'

        if (not company or company.lower() in comp.lower()) and (not city or city.lower() in location.lower()):
            jobs.append({'title': title, 'company': comp, 'salary': salary, 'experience': exp, 'city': location})
            insert_job(title, comp, salary, exp, location)
    return jobs

def parse_avito(job_title, city, company):
    jobs = []
    url = f'https://www.avito.ru/{city}/vakansii?q={job_title}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for item in soup.find_all('div', class_='iva-item-content'):
        title_elem = item.find('a', class_='link-link-MbQDP')
        comp_elem = item.find('div', class_='iva-item-text-Ge6dR')
        salary_elem = item.find('div', class_='price-price-E1Y7h')

        title = title_elem.text if title_elem else 'Не указано'
        comp = comp_elem.text.strip() if comp_elem else 'Не указано'
        salary = salary_elem.text.strip() if salary_elem else 'Не указано'
        exp = "Опыт не указан"
        location = city

        if (not company or company.lower() in comp.lower()):
            jobs.append({'title': title, 'company': comp, 'salary': salary, 'experience': exp, 'city': location})
            insert_job(title, comp, salary, exp, location)
    return jobs

def parse_habr_career(job_title, city, company):
    jobs = []
    url = f'https://career.habr.com/vacancies?q={job_title}'
    if city:
        url += f'&city_id={city}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for item in soup.find_all('div', class_='vacancy-card__inner'):
        title_elem = item.find('a', class_='vacancy-card__title-link')
        comp_elem = item.find('a', class_='link-companies')
        salary_elem = item.find('div', class_='vacancy-card__salary')
        exp_elem = item.find('div', class_='vacancy-card__meta')

        title = title_elem.text if title_elem else 'Не указано'
        comp = comp_elem.text.strip() if comp_elem else 'Не указано'
        salary = salary_elem.text.strip() if salary_elem else 'Не указано'
        exp = exp_elem.text.strip() if exp_elem else 'Не указано'
        location = city

        if (not company or company.lower() in comp.lower()):
            jobs.append({'title': title, 'company': comp, 'salary': salary, 'experience': exp, 'city': location})
            insert_job(title, comp, salary, exp, location)
    return jobs

@app.route('/')
def index():
    return render_template('findJob.html')

@app.route('/search')
def search():
    job_title = request.args.get('job_title')
    city = request.args.get('city')
    company = request.args.get('company')

    jobs = parse_hh_ru(job_title, city, company)
    jobs.extend(parse_avito(job_title, city, company))
    jobs.extend(parse_habr_career(job_title, city, company))

    return jsonify({'jobs': jobs})

@app.route('/all_jobs')
def all_jobs():
    jobs = query_db('SELECT * FROM jobs')
    return jsonify({'jobs': jobs})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
