FROM ckan/ckan-base:2.11

USER root

RUN  pip3 install  -e "git+https://github.com/ckan/ckanext-scheming.git#egg=ckanext-scheming" && \
    pip3 install -e 'git+https://github.com/ckan/ckanext-pdfview#egg=ckanext-pdfview'

COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/01_setup_datapusher.sh /docker-entrypoint.d/
COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/03_setup_scheming.sh /docker-entrypoint.d/
COPY --chown=ckan-sys:ckan-sys ckan/patches ${APP_DIR}/patches
COPY ckan/ckan_dataset_schema.yaml ${APP_DIR}/src/ckanext-scheming/ckanext/scheming

COPY --chown=ckan-sys:ckan-sys src/ckanext-abc /srv/app/src_extensions/ckanext-abc
RUN pip3 install -e /srv/app/src_extensions/ckanext-abc


#

RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done
