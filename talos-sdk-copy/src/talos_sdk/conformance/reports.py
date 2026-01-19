import xml.etree.ElementTree as ET


class JUnitReport:
    def __init__(self) -> None:
        self.testsuites: list[ET.Element] = []

    def add_testsuite(
        self,
        name: str,
        tests: int = 0,
        failures: int = 0,
        errors: int = 0,
        time: float = 0.0,
    ) -> ET.Element:
        suite = ET.Element(
            "testsuite",
            {
                "name": name,
                "tests": str(tests),
                "failures": str(failures),
                "errors": str(errors),
                "time": f"{time:.4f}",
            },
        )
        self.testsuites.append(suite)
        return suite

    def add_testcase(
        self, suite: ET.Element, name: str, classname: str, time: float = 0.0
    ) -> ET.Element:
        case = ET.SubElement(
            suite,
            "testcase",
            {"name": name, "classname": classname, "time": f"{time:.4f}"},
        )
        return case

    def add_failure(
        self, case: ET.Element, message: str, type: str = "AssertionError"
    ) -> None:
        failure = ET.SubElement(case, "failure", {"message": message, "type": type})
        failure.text = message

    def add_error(self, case: ET.Element, message: str, type: str = "Error") -> None:
        error = ET.SubElement(case, "error", {"message": message, "type": type})
        error.text = message

    def write(self, path: str) -> None:
        root = ET.Element("testsuites")
        for suite in self.testsuites:
            root.append(suite)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(path, encoding="utf-8", xml_declaration=True)
