import logging, os, random, re, string, sys

DIR_PATH    = os.path.abspath('')
EXTRA_PATHS = [os.path.join(DIR_PATH, '../libs'),
               os.path.join(DIR_PATH, '../src'),
               os.path.join(DIR_PATH, '../libs/tornado')]
sys.path = EXTRA_PATHS + sys.path

import models

def generate_random_allergies ():
    choices = ['pennicilin', 'pollen', 'streptocaucus']
    return '\n'.join(random.sample(choices, random.randint(1, len(choices))))

def generate_old_diagnosis ():
    diag = 'Ipsum Lorem Dictum scrotum'
    num = random.randint(1, 3)
    ret = [diag]
    for i in range(num):
        ret.append(diag)

    return '\n'.join(ret)

def add_uscongressmen_as_patients (session):
    patients_file = os.path.join(DIR_PATH, 'uscongress.txt')

    ## Each line has the following information. We are keen to retain only the
    ## relevant stuff. We auto-generate the relation contact name and number.

    # District	Name	Party	DC Office	DC Voice	District Voice
    # Electronic Correspondence	Web
    with open(patients_file, 'r') as f:
        line = f.readline()
        fields = line.split('\t')

        while True:
            line = f.readline()
            fields = line.split('\t')
            if line == '':
                break

            logging.debug('Processing %s...', fields[1])
            names  = fields[1].split()         # To construct Relative's Name
            gender = random.choice(['Female', 'Male'])
            allergies = generate_random_allergies()
            old_diag  = generate_old_diagnosis()
            free = random.choice([True, False])
            reg_fee = random.choice([20, 50, 100]) if free else 0

            pat = models.Patient(name=fields[1],
                                 age=random.randint(30, 80),
                                 gender=gender,
                                 title='Mr.' if gender == 'Male' else 'Ms.',
                                 phone=fields[4],
                                 address=fields[3],
                                 email=fields[6],
                                 relative=(random.choice(['John', 'Jill']) +
                                           ' ' + random.choice(names)),
                                relative_phone=fields[5],
                                relative_relation='Friend',
                                free=free,
                                reg_fee=reg_fee,
                                allergies=allergies,
                                old_diag=old_diag
                )
            session.add(pat)

        session.commit()

def add_departments_from_file (session, depts_file):
    with open(depts_file, 'r') as f:
        line = string.strip(f.readline())

        while True:
            line = string.strip(f.readline())
            if line == '':
                break

            logging.debug('Processing %s...', line)
            dept = models.Department(name=line)
            session.add(dept)

        session.commit()

def gen_random_hours ():
    """Generate and return a string of random consultation hours in a comma
    separated format.

    - Four digit times in 24-hr format
    - comma separated values for each day
    - Within each day there can be one or more ranges times separated by
      spaces

    Starts on Sunday

    E.g. 0900-1000 1500-1700 means there are two consultations on that day.
    """

    values = ['0900-1000', '1000-1200', '1200-1300', '1400-1600', '1600-1730']

    ret = []
    for i in range(7):
        num = random.randint(1, 3)
        cons = random.sample(values, num)
        ret.append(' '.join(cons))

    return ','.join(ret)

def add_doctor_names (session, doctors_file):
    ph_lower = 7000000000
    ph_upper = 9999999999

    with open(doctors_file, 'r') as f:
        line = f.readline()

        while True:
            line = string.strip(f.readline())
            if line == '':
                break

            names = line.split()
            for name in names:
                if len(name) > 2:
                    n = name
                    break

            logging.debug('Processing %s...', line)
            res = re.search('^Dr\. (.*)', line)
            if res:
                line = res.group(1)

            doc = models.Doctor(title='Dr.',
                                name=line,
                                phone=str(random.randint(ph_lower, ph_upper)),
                                email=n + '@mentalasylum.in')
            session.add(doc)

        session.commit()

def add_slots (session):
    for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                'Friday', 'Saturday']:
        for shift in ['Morning', 'Afternoon']:
            hour = models.Slot(day=day, shift=shift)
            session.add(hour)

    session.commit()

def get_random_times ():
    min = 9
    max = 17
    start = random.randint(min, max-1)
    end   = random.randint(start, max)

    return ('%02d00' % start), ('%02d00' % end)

def add_doc_hours (session):
    q = session.query(models.Doctor)
    for doc in q:
        start, end = get_random_times()
        hour = models.Hour(doctor_id=doc.id, start_time=start, end_time=end)
        session.add(hour)

    session.commit()

def add_departments (session):
    q = session.query(models.Doctor)
    doc_cnt = q.count()
    doc_ids = [doc.id for doc in q]

    i = 0
    q = session.query(models.Department)
    while True:
        try:
            for dept in q:
                doc_id = doc_ids[i]
                p = session.query(models.Doctor)
                doc = p.filter_by(id = doc_id).first()
                logging.debug('i = %3d; Adding Doc (%-20s) to Dept (%s)...',
                              i, doc.name, dept.name)
                dept.doctors.append(doc)
                i += 1
        except Exception, e:
            logging.info('Caught exception (%s) breaking.', e)
            break

    session.commit()        

def add_consultations (session):
    logging.debug('')
    p = session.query(models.Doctor)
    docs = [doc for doc in p]

    q = session.query(models.Patient)
    for pat in q:
        logging.debug('Adding visits to patient: %s...', pat.name)
        num = random.randint(1, 3)
        for i in range(num):
            charge = random.choice([10, 20, 30, 40, 50])
            con = models.Consultation(charge=charge,
                                      notes='Lorem Ipsum Gypsum zero sum')
            doc = random.choice(docs)
            logging.debug('\tAdded doctor ID: %3d, Name: %s...',
                          doc.id, doc.name)
            pat.consultations.append(con)
            doc.consultations.append(con)

    session.commit()

def main ():
    logging.getLogger().setLevel(logging.DEBUG)

    logging.info('Settingup schema and tables....')
    engine, session = models.setup_tables("sample.db")

    logging.info('Importing US Congressmen as Patients...')
    add_uscongressmen_as_patients(session)

    logging.info('Importing department names from file...')
    add_departments_from_file(session, 'depts.txt')

    logging.info('Adding default consulting hour slots...')
    add_slots(session)

    logging.info('Adding TN MLAs as doctors...')
    add_doctor_names(session, 'tnmlas.txt')

    logging.info('Setting up Consulting Hours...')
    add_doc_hours(session)

    logging.info('Assigning Departments to doctors...')
    add_departments(session)

    logging.info('Setting up random visits...')
    add_consultations(session)

if __name__ == '__main__':
    main()
