import pandas as pd
import numpy as np
from watchtower.handlers_ import GithubDatabase
from watchtower.commits_ import find_word_in_string
from watchtower._config import DATETIME_FORMAT

db = GithubDatabase(auth='GITHUB_API')
users = [ii for ii in db.users if len(ii) > 0]
search_queries = ['DOC', 'docs', 'docstring',
                  'documentation', 'docathon', 'readme', 'guide', 'tutorial']

# Times for inclusion
start = '2017-03-01'
end = '2017-03-11'
print('Calculating user activity from {} to {}'.format(start, end))

start, end = [pd.to_datetime(ii).tz_localize('US/Pacific')
              for ii in [start, end]]
exceptions = []
activity = []
for user in users:
    try:
        user_db = db.load(user)

        if len(user_db.PushEvent) == 0:
            activity.append((user, np.nan, np.nan))
            print('No commits for user: {}'.format(user))
            continue

        messages, dates = zip(*[(jj['message'], idate)
                              for idate, ii in user_db.PushEvent.iterrows()
                              for jj in ii['payload']['commits']])
        dates = list(dates)
        for ii, idate in enumerate(dates):
            if idate.tzinfo is None:
                idate = idate.tz_localize('UTC')
            idate = idate.tz_convert('US/Pacific')
            dates[ii] = idate
        dates = np.array(dates)
        messages = np.array(messages)
        mask = (dates > start) * (dates <= end)
        messages = messages[mask]
        dates = dates[mask]
        for message, date in zip(messages, dates):
            is_doc = find_word_in_string(message, search_queries)
            activity.append((user, date, is_doc))

    except Exception as e:
        exceptions.append((user, e))
        activity.append((user, np.nan, np.nan))
        continue
print('Exceptions: ', '\n'.join([str(ii) for ii in exceptions]))
activity = pd.DataFrame(activity, columns=['user', 'date', 'is_doc'])
activity = activity.set_index('date')
activity.to_csv('.user_totals.csv', date_format=DATETIME_FORMAT)
