FROM ckan/ckan-base:2.11

USER root

COPY ckan/requirements.txt ${APP_DIR}/requirements.txt
RUN pip3 install -r ${APP_DIR}/requirements.txt

COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/01_setup_datapusher.sh /docker-entrypoint.d/
COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/03_setup_scheming.sh /docker-entrypoint.d/
COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/04_setup_portal.sh /docker-entrypoint.d/
COPY --chown=ckan-sys:ckan-sys ckan/patches ${APP_DIR}/patches

COPY --chown=ckan-sys:ckan-sys src/ckanext-mpb /srv/app/src_extensions/ckanext-mpb
RUN pip3 install -e /srv/app/src_extensions/ckanext-mpb


#

RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done
