import logging

# import zaza.model


def _check_run_result(result, codes=None):
    if not result:
        raise Exception("Failed to get a result.")
    allowed_codes = list("0")

    if codes:
        allowed_codes.extend(codes)

    if result["Code"] not in allowed_codes:
        logging.error(
            "Bad result code received. Result code: {}".format(result["Code"])
        )
        logging.error("Returned: \n{}".format(result))
        raise Exception("Command returned non-zero return code.")
