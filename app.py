from flask import Flask, request, render_template, redirect, url_for, session
import virtualbox as vb
import secrets, os

class User:
    def __init__(self, username, password, sudo):
        self.username = username
        self.password = password
        self.sudo = sudo


    def __repr__(self):
        return "<User: {}>".format(self.username)


app = Flask(__name__)
app.secret_key = "1"
vbox = vb.VirtualBox()
users = []
accessibility = {}
session = {"token": None}

users.append(User(username="admin", password="1234", sudo=True))
users.append(User(username="user1", password="4444", sudo=False))



def check_access(vm_name):
    if not (session['token'] and (accessibility[session['token']] or vm_name == "vm1")):
        return False
    return True

@app.route('/', methods=['GET', 'POST'])
def hello_world():

    if request.method == "GET":
        return render_template('homePage.html')
    else:
        username = request.form["username"]
        password = request.form["password"]
        user = [x for x in users if (x.username == username and x.password == password)]
        if len(user) > 0:
            token = secrets.token_hex(3)
            session['token'] = token
            print(session['token'])
            accessibility[token] = [x for x in users if x.username == username][0].sudo
            return "Hi {}! You Have {} Virtual Machines".format(username, len(vbox.machines))
        else:
            return redirect(url_for('hello_world'))


@app.route('/list')
def get_list():
    if not session["token"]:
        return redirect(url_for('hello_world'))
    # print(request.headers["token"])
    ls = {}
    for m in vbox.machines:
        ls[m.name] = str(m.state)
    return ls


@app.route('/start_<name>')
def start_machine(name):
    if not check_access(name):
        return "sorry! you don't have permission for this."
    machine = vbox.find_machine(name)
    os.system('cmd /c "vboxmanage startvm {}'.format(name))
    print(machine.cpu_count)
    return "status : {} has started ".format(name)


@app.route('/status_<name>')
def get_status_list(name):
    if not check_access(name):
        return "sorry! you don't have permission for this."
    m = vbox.find_machine(name_or_id=name)
    return "{} status is : {}".format(name, str(m.state))


@app.route('/cpu_count', methods=['GET', 'POST'])
def set_cpu_count():
    if not session["token"]:
        return redirect(url_for('hello_world'))
    if request.method == 'POST':
        name = request.form['name']
        number = int(request.form['number'])
        memory = int(request.form['memory'])
        if not check_access(name):
            return "sorry! you don't have permission for this."
        os.system('cmd /c "vboxmanage modifyvm {} --cpus {}"'.format(name, number))
        os.system('cmd /c "vboxmanage modifyvm {} --memory {}"'.format(name, memory))
        m = vbox.find_machine(name_or_id=name)
        return "{} : cpu count = {} | memory = {}".format(name, m.cpu_count, m.memory_size)
    else:
        return render_template("cpu_count.html")


@app.route('/shutdown_<name>')
def shutdown(name):
    if not check_access(name):
        return "sorry! you don't have permission for this."
    os.system('cmd /c "vboxmanage controlvm {} poweroff"'.format(name))
    return get_status_list(name)


@app.route('/clone', methods=['POST', 'GET'])
def clone():
    if not session["token"]:
        return redirect(url_for('hello_world'))

    if request.method == 'POST':
        target_name = request.form['target_name']
        new_vm = request.form['new_vm']
        if not check_access(target_name):
            return "sorry! you don't have permission for this."
        os.system('cmd /c "vboxmanage clonevm {} --name={}  --register'.format(target_name, new_vm))

        return redirect(url_for('get_list'))
    else:
        return render_template("clone.html")


@app.route('/delete', methods=['POST', 'GET'])
def delete_vm():
    if not session["token"]:
        return redirect(url_for('hello_world'))

    if request.method == 'POST':
        target_name = request.form['target_name']
        if not check_access(target_name):
            return "sorry! you don't have permission for this."
        os.system('cmd /c "vboxmanage unregistervm {} --delete'.format(target_name))

        return redirect(url_for('get_list'))
    else:
        return render_template("delete_vm.html")



if __name__ == '__main__':
    app.run()
