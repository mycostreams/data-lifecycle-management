FROM fiji/fiji:latest

COPY ./scripts /opt/fiji/scripts

COPY --chown=fiji:fiji ./stitch-start.sh ./stitch-start.sh
RUN chmod +x ./stitch-start.sh

CMD ["./stitch-start.sh"]

