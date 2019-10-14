from flask import Flask, render_template, Response, request
import requests
import json
import datetime

app = Flask(__name__)
start_date_param = 'start'
end_date_param = 'end'
GITLAB_API_URL = 'https://gitlab.com/api/v4/projects/"YOUR PROJECT"/issues'
TOKEN = '"YOUR_PRIVATE_TOKEN"'


class Issue:
    def __init__(self, iid, closed_user_name, closed_date):
        self.iid = iid
        self.closed_user_name = closed_user_name
        self.closed_date = closed_date


@app.route('/')
def index() -> str:
    return render_template('main.html')


@app.route('/get_completed_issue_num_per_user', methods=['GET'])
def count_completed_issue_per_user():
    start_date_text = request.args.get(start_date_param)
    if start_date_text is not None:
        start_date = datetext_to_datetme(start_date_text.strip('"'))
    else:
        start_date = None

    end_date_text = request.args.get(end_date_param)
    if end_date_text is not None:
        end_date = datetext_to_datetme(end_date_text.strip('"'))
    else:
        end_date = None

    completed_issues = [x for x in get_completed_issues_from_gitlab(GITLAB_API_URL) if is_closed_between(x, start_date, end_date)]
    count_result = count_issues_per_user(completed_issues)
    count_result_json = count_result_to_json(count_result)
    return Response(count_result_json)


def count_result_to_json(count_result_dic):
    json_items = []

    if len(count_result_dic.keys()) > 0:
        for key in count_result_dic.keys():
            json_items.append("{" + "name:'{0}', count:'{1}'".format(key, count_result_dic[key]) + "}")
        return "[" + ",".join(json_items) + "]"
    else:
        return ""

def is_closed_between(issue, start=None, end=None):
    if start is None:
        if end is None:
            return True
        else:
            return issue.closed_date.date() <= end.date()
    else:
        if end is None:
            return start.date() <= issue.closed_date.date()
        else:
            return start.date() <= issue.closed_date.date() and issue.closed_date.date() <= end.date()


def count_issues_per_user(issues):
    user_to_issue_num_dic = {}
    for issue in issues:
        if issue.closed_user_name not in user_to_issue_num_dic.keys():
            user_to_issue_num_dic[issue.closed_user_name] = 0
        user_to_issue_num_dic[issue.closed_user_name] += 1

    return user_to_issue_num_dic


def get_completed_issues_from_gitlab(url):
    completed_issues = []
    params = {'state': 'closed', 'scope': 'all'}
    headers = {'PRIVATE-TOKEN': TOKEN}
    issues_json = requests.get(url, params=params, headers=headers).text
    for issue_dic in json.loads(issues_json):
        iid = issue_dic['iid']
        closed_date = datetime_text_to_datetime(issue_dic['closed_at'])
        closed_user_name = issue_dic['closed_by']['name']
        completed_issues.append(Issue(iid, closed_user_name, closed_date))

    return completed_issues


def datetext_to_datetme(date_text):
    return datetime.datetime.strptime(date_text, '%Y-%m-%d')


def datetime_text_to_datetime(time_text):
    return datetime.datetime.strptime(time_text, '%Y-%m-%dT%H:%M:%S.%fZ')


if __name__ == '__main__':
    app.run()
