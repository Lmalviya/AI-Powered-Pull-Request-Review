import sys
import os
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
# Note: we mock the dependencies of main/worker to avoid side effects
with patch("services.orchestrator.main.setup_logging"):
    from services.orchestrator.main import worker_loop

@pytest.mark.asyncio
async def test_worker_loop_start_pr_review():
    """
    Test that the worker loop correctly handles a START_PR_REVIEW action.
    """
    # Mocking task data
    mock_task = {
        "action": "START_PR_REVIEW",
        "review_request_id": "test-req-123",
        "repo": "owner/repo",
        "pr_number": 1
    }

    # Mocking queue_manager.dequeue to return a task then None (to break loop)
    # We use a side_effect to return the task once, then raise an exception or stop
    with patch("services.orchestrator.main.queue_manager") as mock_queue:
        with patch("services.orchestrator.main.workflow_manager") as mock_workflow:
            mock_queue.dequeue.side_effect = [mock_task, None]
            
            # Since worker_loop is a 'while True' loop, we need a way to stop it.
            # We'll use a timeout and cancel the task.
            try:
                task = asyncio.create_task(worker_loop())
                # Give it enough time to process one item
                await asyncio.sleep(0.1) 
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            except Exception:
                pass

            # Assertions
            mock_workflow.pr_review_workflow.assert_called_once_with(mock_task)

@pytest.mark.asyncio
async def test_worker_loop_evaluate_chunk():
    """
    Test that the worker loop correctly handles an EVALUATE_CHUNK action.
    """
    mock_task = {
        "action": "EVALUATE_CHUNK",
        "chunk_id": "chunk-456"
    }

    with patch("services.orchestrator.main.queue_manager") as mock_queue:
        with patch("services.orchestrator.main.workflow_manager") as mock_workflow:
            mock_queue.dequeue.side_effect = [mock_task, None]
            
            try:
                task = asyncio.create_task(worker_loop())
                await asyncio.sleep(0.1)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            except Exception:
                pass

            mock_workflow.evaluate_chunk.assert_called_once_with(mock_task)

@pytest.mark.asyncio
async def test_worker_loop_unknown_action():
    """
    Test that the worker loop handles unknown actions gracefully.
    """
    mock_task = {
        "action": "UNKNOWN_ACTION"
    }

    with patch("services.orchestrator.main.queue_manager") as mock_queue:
        with patch("services.orchestrator.main.workflow_manager") as mock_workflow:
            with patch("services.orchestrator.main.logger") as mock_logger:
                mock_queue.dequeue.side_effect = [mock_task, None]
                
                try:
                    task = asyncio.create_task(worker_loop())
                    await asyncio.sleep(0.1)
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                except Exception:
                    pass

                mock_logger.warning.assert_called_with("Unknown action received: %s", "UNKNOWN_ACTION")
                mock_workflow.pr_review_workflow.assert_not_called()
                mock_workflow.evaluate_chunk.assert_not_called()
