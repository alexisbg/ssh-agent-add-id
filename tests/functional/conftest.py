from typing import List, Optional

from pytest import Config, Item, Mark, Session


def pytest_configure(config: Config) -> None:
    """The Pytest hook to perform initial configuration."""
    # Regiter the custom mark
    config.addinivalue_line("markers", "after_test(test_name): force test to run after another one")


def pytest_collection_modifyitems(session: Session, config: Config, items: List[Item]) -> None:
    """The Pytest hook to modify the list of collected tests."""
    _after_test_mark(items)


def _after_test_mark(items: List[Item]) -> None:
    """Move tests with after_test mark after the given test(s).

    Args:
        items (List[Item]): The list of test collection.
    """
    for i in range(len(items)):
        after_test_mark: Optional[Mark] = items[i].keywords.get("after_test")

        # The current test has after_test mark
        if after_test_mark:
            before_tests = [i for i in items if i.name.startswith(str(after_test_mark.args[0]))]

            # The tests that must be run before are in the collection
            if before_tests:
                last_index = items.index(before_tests[-1])

                # The current marked test is before the last wanted test instead of after
                if i < last_index:
                    item = items.pop(i)
                    items.insert(last_index, item)
                    # Recall _after_test_mark with the modified item list
                    _after_test_mark(items)
                    # Stop here because the item list has been modified
                    break
