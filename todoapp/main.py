from __future__ import print_function

import os
import sys
from time import sleep
from os import environ
from socket import socket
from traceback import format_tb
from socket import AF_INET, SOCK_STREAM


from circuits.web.errors import httperror
from circuits.web import Controller, Server
from circuits.web.exceptions import NotFound
from circuits import handler, Event, Component

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from redisco import connection_setup, get_client


from models import TodoItem, TodoList


DEFAULTS = {
    "appname": "todoapp",
    "version": "dev",
}


class render(Event):
    """render Event"""


class JinjaTemplate(object):

    def __init__(self, _name, **context):
        self._name = _name
        self.context = context

    @property
    def name(self):
        return self._name


class JinjaRenderer(Component):

    channel = "web"

    def init(self, path, defaults=None):
        self.path = path
        self.defaults = defaults or {}

        self.env = Environment(loader=FileSystemLoader(path))

    @handler("response", priority=1.0)
    def serialize_response_body(self, event, response):
        template = response.body
        if not isinstance(template, JinjaTemplate):
            return

        try:
            request = response.request

            try:
                tmpl = self.env.get_template("{0}.html".format(template.name))
            except TemplateNotFound:
                raise NotFound()

            ctx = self.defaults.copy()
            ctx.update({"request": request, "response": response, "uri": request.uri})

            ctx.update(template.context)

            response.body = tmpl.render(**ctx)
        except:
            event.stop()
            evalue, etype, etraceback = sys.exc_info()
            error = (evalue, etype, format_tb(etraceback))
            self.fire(httperror(request, response, 500, error=error))


class Root(Controller):

    def GET(self, *args, **kwargs):
        name = (args and args[0]) or "TODO"
        todo = TodoList.objects.get_or_create(name=name)
        entries = [entry for entry in todo.entries if not entry.done]
        return JinjaTemplate("views/index", name=name, entries=entries)


class Add(Controller):

    channel = "/add"

    def GET(self, *args, **kwargs):
        return JinjaTemplate("views/add")

    def POST(self, *args, **kwargs):
        name = (args and args[0]) or "TODO"
        todo = TodoList.objects.get_or_create(name=name)
        todo.add_entry(kwargs["title"])
        return self.redirect(self.uri("/"))


class Update(Controller):

    channel = "/update"

    def done(self, *args, **kwargs):
        id = int(kwargs["id"])
        item = TodoItem.objects.get_by_id(id)
        item.mark_done()
        return self.redirect(self.uri("/"))


def waitfor(host, port, timeout=10):
    sock = socket(AF_INET, SOCK_STREAM)

    while sock.connect_ex((host, port)) != 0 and timeout:
        timeout -= 1
        sleep(1)

    if timeout <= 0:
        print("Timed out waiting for {0:s}:{1:d}".format(host, port))
        raise SystemExit(1)


def setup_database():
    dbhost = environ.get("REDIS_PORT_6379_TCP_ADDR", "localhost")
    dbport = int(environ.get("REDIS_PORT_6379_TCP_PORT", "6379"))

    print("Waiting for Redis Service on {0:s}:{1:d} ...".format(dbhost, dbport))

    waitfor(dbhost, dbport)

    print("Connecting to Redis on {0:s}:{1:d} ...".format(dbhost, dbport))

    connection_setup(host=dbhost, port=dbport)

    print("Success!")

    db = get_client()

    return db


class TodoApp(Component):

    def init(self, db):
        self.db = db

        Server(("0.0.0.0", 8000)).register(self)
        JinjaRenderer("templates", defaults=DEFAULTS).register(self)

        Root().register(self)
        Add().register(self)
        Update().register(self)

    def stopped(self, *args):
        print("Shutting down...")
        self.db.save()


def main():
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)

    db = setup_database()

    TodoApp(db).run()


if __name__ == "__main__":
    main()
