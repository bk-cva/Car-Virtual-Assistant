class ConfigSchema:
    def __init__(self,
                 here_api_key,
                 nlu_url,
                 cva_db_url,
                 calendar_id,
                 do_call_external_nlu,
                 schedule_api_dry_run,
                 timezone):
        self.here_api_key = here_api_key
        self.nlu_url = nlu_url
        self.cva_db_url = cva_db_url
        self.calendar_id = calendar_id
        self.do_call_external_nlu = do_call_external_nlu
        self.schedule_api_dry_run = schedule_api_dry_run
        self.timezone = timezone
