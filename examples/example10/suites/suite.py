import os.path as osp

import lemoncheesecake.api as lcc


@lcc.suite("Suite")
class suite(object):
    @lcc.test("Test")
    def test(self, project_dir):
        # image from https://pixabay.com/en/cake-lemon-sweet-yellow-food-2700645/
        image_path = osp.join(project_dir, "cake.jpg")

        lcc.set_step("Attachment")
        lcc.save_attachment_file(image_path)

        lcc.set_step("Image attachment")
        lcc.save_image_file(image_path)
