FROM python:2.7-onbuild

EXPOSE 8000/tcp

CMD ["todoapp"]

RUN python setup.py install
