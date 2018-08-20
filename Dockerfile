FROM debian:stretch

RUN groupadd --gid 1000 -r explorer && useradd --uid 1000 --create-home --system -g explorer explorer \
	&& mkdir -p /explorer

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONPATH=/explorer

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   python-pip \
	   libpq-dev \
	   postgresql-client \
	   build-essential \
	   libpython2.7 \
	   python-dev \
	   wget \
	&& apt-get clean \
	&& pip install virtualenv
# Note: we're installing libpython2.7 because uWSGI needs it on runtime (crashes if it can't find it)

RUN su explorer -c "virtualenv /home/explorer/env"

COPY ./requirements /home/explorer/requirements
ARG INSTALL_REQUIREMENTS=production
RUN su explorer -c ". /home/explorer/env/bin/activate && \
	pip install --no-cache-dir -r /home/explorer/requirements/$INSTALL_REQUIREMENTS.pip && \
	rm -rf /home/explorer/.cache"

RUN apt-get purge -y python-dev build-essential libpq-dev && apt-get autoremove -y

COPY . /explorer

WORKDIR /explorer

# Always make the project virtualenv active
ENV VIRTUAL_ENV=/home/explorer/env \
	PATH=/home/explorer/env/bin:$PATH \
	FLASK_APP=app.py

EXPOSE 5000

USER explorer

HEALTHCHECK --interval=1m --timeout=3s CMD wget --content-on-error -qO- http://localhost:5000/header || exit 1

CMD ["flask", "run", "--host=0.0.0.0"]
