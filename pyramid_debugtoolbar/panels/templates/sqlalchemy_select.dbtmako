<div class="pDebugPanelTitle">
	<a class="pDebugClose pDebugBack" href="">Back</a>
	<h3>SQL Select</h3>
</div>
<div class="pDebugPanelContent">
	<div class="scroll">
		<dl>
			<dt>Executed SQL</dt>
			<dd>${sql|n}</dd>
			<dt>Time</dt>
			<dd>${'%.4f' % (duration)} ms</dd>
		</dl>
		% if result:
		<table class="djSqlExplain">
			<thead>
				<tr>
					% for h in headers:
						<th>${h.upper()}</th>
					% endfor
				</tr>
			</thead>
			<tbody>
				% for i, row in enumerate(result):
				    <tr class="${i%2 and 'pDebugEven' or 'pDebugOdd'}">
						% for column in row:
						<td>${column}</td>
						% endfor
					</tr>
				% endfor
			</tbody>
		</table>
		% else:
		<p>Empty set</p>
		% endif
	</div>
</div>