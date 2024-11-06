
Feature: Upload flow
    @fixture.client
    @fixture.get_exports
    Scenario: New event added
        Given the containers are running
        When an event is added
        Then the export count should be incremented
