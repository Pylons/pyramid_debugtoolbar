% if renderings:
% for rendering in renderings:
<table>
	<thead>
		<tr>
			<th colspan="2">Renderer Name</th>
		</tr>
	</thead>
	<tbody>
		<tr class="pDebugOdd">
			<td colspan="2">${rendering['name']|h}</td>
		</tr>
	</tbody>
	<thead>
		<tr>
			<th colspan="2">Rendering Value</th>
		</tr>
	</thead>
	<tbody>	
		<tr class="pDebugOdd">
			<td colspan="2">${rendering['val']|h}</td>
		</tr>
	</tbody>
	<thead>
		<tr>
			<th colspan="2">System Values</th>
		</tr>
	</thead>
	<tbody>	
		% for i, (key, value) in enumerate(rendering['system']):
		<tr class="${i%2 and 'pDebugEven' or 'pDebugOdd'}">
			<td>${key|h}</td>
			<td>${value|h}</td>
		</tr>
		% endfor
	</tbody>
</table>
% endfor
% else:
<p>No renderings performed.</p>
% endif


