from redisco.models import Model
from redisco.models import Attribute, BooleanField, ListField


class TodoList(Model):

    name = Attribute(required=True)
    entries = ListField("TodoItem")

    def delete(self):
        for entry in self.entries:
            entry.delete()
        super(TodoList, self).delete()

    def add_entry(self, title):
        entry = TodoItem(title=title)
        entry.save()
        self.entries.append(entry)
        self.save()

    class Meta:
        indicies = ("id", "name",)


class TodoItem(Model):

    title = Attribute(required=True)
    done = BooleanField(default=False)

    def mark_donw(self):
        self.done = True
        self.save()

    class Meta:
        indicies = ("id", "title", "done",)
