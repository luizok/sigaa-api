import json
import os

from dotenv import load_dotenv

from sigaa_api import SigaaAPI


if __name__ == '__main__':

    load_dotenv()

    api = SigaaAPI()
    api.authorize(
        os.getenv('SIGAA_USERNAME'),
        os.getenv('SIGAA_PASSWORD')
    )

    v = api.get_vinculos()
    api.set_current_vinculo(1)
    api.get_all_matrizes(3325058)

    g = api.get_grade_curricular(33250650)

    with open('cadeiras.json', 'w') as f:
        json.dump(g, f, indent=4, ensure_ascii=False)
