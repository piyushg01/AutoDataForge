// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DataAudit {
	struct AuditRecord {
		string datasetId;
		string datasetHash;
		string action;
		uint256 timestamp;
		address actor;
	}

	mapping(string => AuditRecord[]) private recordsByDataset;

	event AuditLogged(
		string indexed datasetId,
		string datasetHash,
		string action,
		uint256 timestamp,
		address indexed actor
	);

	function logAudit(string calldata datasetId, string calldata datasetHash, string calldata action) external {
		AuditRecord memory record = AuditRecord({
			datasetId: datasetId,
			datasetHash: datasetHash,
			action: action,
			timestamp: block.timestamp,
			actor: msg.sender
		});

		recordsByDataset[datasetId].push(record);
		emit AuditLogged(datasetId, datasetHash, action, block.timestamp, msg.sender);
	}

	function getAuditCount(string calldata datasetId) external view returns (uint256) {
		return recordsByDataset[datasetId].length;
	}

	function getAuditRecord(string calldata datasetId, uint256 index) external view returns (AuditRecord memory) {
		require(index < recordsByDataset[datasetId].length, "Invalid index");
		return recordsByDataset[datasetId][index];
	}
}
