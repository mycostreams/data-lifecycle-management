
Feature: Upload flow
    @fixture.client
    @fixture.db_engine
    Scenario: New timestep added
        Given the watcher and worker are running
        When a timestep is added
        Then the results are stored locally
        And the processed timestep is available in the object store
